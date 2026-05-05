"""
一人公司协作流 · workflow

灵感:一人公司架构 v1.8.0 的 7 步项目入口 SOP + R07 CKO 四型蒸馏。

LangGraph 拓扑:
    START
      ↓
    [triage]  R07 CKO 分诊员 · 出"分诊提案"(档位/类型/协作链)
      ↓
    [worker_0]  第一棒
      ↓
    [worker_1]  第二棒
      ↓
    ... 按 specialist_agent_ids 顺序串
      ↓
    [worker_N-1]  最后一棒
      ↓
    [distill]  R07 CKO 四型闭环蒸馏 · 五路径回写
      ↓
     END
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TypedDict

from fastapi import HTTPException
from langgraph.graph import END, START, StateGraph

from ...harness import (
    assemble_persona_prompt,
    post_hook_update_libraries,
)
from ...runtime import call_llm, llm_gateway
from ...schemas import (
    AgentDefinition,
    RunArtifacts,
    TraceEvent,
    WorkflowDefinition,
    WorkflowGraph,
    WorkflowRunResponse,
)
from ...store import InMemoryPlaygroundStore
from ..langgraph_adapter import workflow_graph_from_compiled
from .prompts import (
    build_distillation_prompt,
    build_fallback_response,
    build_triage_prompt,
    build_worker_prompt,
)


TRIAGE_NODE = "triage"
DISTILL_NODE = "distill"


class OPCState(TypedDict, total=False):
    user_input: str
    triage_proposal: str
    worker_outputs: list  # list[tuple[str, str]]  -- (agent_name, output)
    distillation: str
    assistant_message: str


def _event(event_type: str, title: str, detail: str, **payload: object) -> TraceEvent:
    return TraceEvent(type=event_type, title=title, detail=detail, payload=payload)


def _worker_node_id(idx: int, agent: AgentDefinition) -> str:
    return f"worker_{idx}_{agent.id}"


def _compile_opc_app(
    workflow: WorkflowDefinition,
    agents: list[AgentDefinition],
    triage_node: Callable[[OPCState], OPCState],
    worker_nodes: list[Callable[[OPCState], OPCState]],
    distill_node: Callable[[OPCState], OPCState] | None,
):
    if not agents:
        raise HTTPException(
            status_code=400,
            detail="one_person_company requires at least 1 agent.",
        )
    if len(worker_nodes) != len(agents):
        raise HTTPException(
            status_code=500,
            detail="worker_nodes count mismatch with agents.",
        )

    builder = StateGraph(OPCState)
    builder.add_node(
        TRIAGE_NODE,
        triage_node,
        metadata={"kind": "logic", "label": "📚 CKO · 分诊提案"},
    )

    for i, agent in enumerate(agents):
        builder.add_node(
            _worker_node_id(i, agent),
            worker_nodes[i],
            metadata={"kind": "agent", "label": f"{i+1}. {agent.name}"},
        )

    use_distill = workflow.finalizer_enabled and distill_node is not None
    if use_distill:
        builder.add_node(
            DISTILL_NODE,
            distill_node,
            metadata={"kind": "final", "label": "📚 CKO · 五路径回写"},
        )

    builder.add_edge(START, TRIAGE_NODE)
    builder.add_edge(TRIAGE_NODE, _worker_node_id(0, agents[0]))
    for i in range(len(agents) - 1):
        builder.add_edge(
            _worker_node_id(i, agents[i]),
            _worker_node_id(i + 1, agents[i + 1]),
        )

    last_worker_id = _worker_node_id(len(agents) - 1, agents[-1])
    if use_distill:
        builder.add_edge(last_worker_id, DISTILL_NODE)
        builder.add_edge(DISTILL_NODE, END)
    else:
        builder.add_edge(last_worker_id, END)

    return builder.compile()


def build_one_person_company_graph(
    workflow: WorkflowDefinition,
    agents: list[AgentDefinition],
) -> WorkflowGraph:
    """给 GET /api/workflows/{id}/graph 用 · 只编图不执行。"""
    if not agents:
        raise HTTPException(
            status_code=400,
            detail="one_person_company requires at least 1 agent.",
        )

    def noop(_: OPCState) -> OPCState:
        return {}

    app = _compile_opc_app(
        workflow,
        agents,
        triage_node=noop,
        worker_nodes=[noop for _ in agents],
        distill_node=noop if workflow.finalizer_enabled else None,
    )
    return workflow_graph_from_compiled(app)


def run_one_person_company(
    store: InMemoryPlaygroundStore,
    workflow: WorkflowDefinition,
    user_input: str,
    history: list[dict[str, str]] | None = None,
    on_event: Callable[[TraceEvent], None] | None = None,
) -> WorkflowRunResponse:
    """实际执行 · 三阶段:CKO 分诊 → 岗位接力 → CKO 蒸馏。"""
    # 解析参与岗位
    agents: list[AgentDefinition] = []
    for agent_id in workflow.specialist_agent_ids:
        a = store.get_agent(agent_id)
        if a is not None:
            agents.append(a)
    if not agents:
        raise HTTPException(
            status_code=400,
            detail="one_person_company requires at least 1 valid agent.",
        )

    trace: list[TraceEvent] = []

    def push(item: TraceEvent) -> None:
        trace.append(item)
        if on_event is not None:
            on_event(item)

    push(_event(
        "run_started",
        "Run Started",
        f"一人公司协作流启动 · {workflow.name} · {len(agents)} 个岗位",
        workflow_id=workflow.id,
        workflow_type=workflow.type,
        agents_count=len(agents),
    ))

    # ---------- 节点定义 ----------
    def triage_node(state: OPCState) -> OPCState:
        push(_event(
            "node_entered",
            "📚 CKO 分诊员上场",
            "R07 CKO 视角 · 项目入口 SOP 第 1-3 步 · 自动出分诊提案",
            node_id=TRIAGE_NODE,
        ))
        try:
            prompt = build_triage_prompt(state["user_input"], agents)
            proposal = call_llm(prompt, temperature=0)
        except Exception as e:
            proposal = (
                "## 分诊提案(降级版 · 无 LLM)\n\n"
                f"**档位**: 🚀 标准档(默认)\n"
                f"**协作链**: {' → '.join(a.name for a in agents)}\n"
                f"**提示**: 配置 OPENAI_API_KEY 可启用 LLM 自动分诊\n"
                f"_错误: {type(e).__name__}_"
            )
        push(_event(
            "route_selected",
            "分诊提案已出",
            f"涉及 {len(agents)} 岗位 · 等执行",
            node_id=TRIAGE_NODE,
            preview=proposal[:200],
        ))
        push(_event(
            "node_exited",
            "📚 CKO 分诊完成",
            "进入岗位接力执行",
            node_id=TRIAGE_NODE,
        ))
        return {
            "triage_proposal": proposal,
            "worker_outputs": [],
        }

    def make_worker_node(idx: int, agent: AgentDefinition):
        node_id = _worker_node_id(idx, agent)

        def worker_node(state: OPCState) -> OPCState:
            push(_event(
                "node_entered",
                f"第 {idx+1} 棒 · {agent.name}",
                f"{agent.name} 接单",
                node_id=node_id,
                agent_id=agent.id,
                step=idx + 1,
                total_steps=len(agents),
            ))
            prior_outputs = list(state.get("worker_outputs", []) or [])

            # ---- Harness Pre-hook · Persona Core 三层拼装 ----
            # 把 agent.system_prompt(永久)+ persona/relationship/guides(累积)
            # 注入到 system role,把 triage + handoff + 召回注入到 user role。
            # 失败时退回原路径,不阻断 workflow。
            agent_for_run = agent
            user_msg = build_worker_prompt(
                user_input=state["user_input"],
                triage_proposal=state.get("triage_proposal", ""),
                prior_outputs=prior_outputs,
                current_agent=agent,
                step_index=idx + 1,
                total_steps=len(agents),
            )
            try:
                assembly = assemble_persona_prompt(
                    agent_id=agent.id,
                    user_input=state["user_input"],
                    workflow_context=state.get("triage_proposal", "")[:1500],
                    handoff_inputs=[
                        {"agent_name": name, "output": out}
                        for name, out in prior_outputs
                    ],
                    recall_limit=5,
                )
                hctx = assembly.harness_context
                # 用 augmented system_prompt 替换 agent 同名字段(其余字段保留)
                agent_for_run = agent.model_copy(
                    update={"system_prompt": assembly.system_prompt}
                )
                user_msg = assembly.user_prompt
                push(_event(
                    "harness_prompt_assembled",
                    f"🧠 Harness · {agent.name} 三层 prompt 已注入",
                    (
                        f"召回 {len(hctx.recalled_events)} 条 · "
                        f"guides {len(hctx.active_guides)} 条 · "
                        f"信任 {hctx.relationship.trust_level:.2f}"
                        if hctx.relationship else
                        f"召回 {len(hctx.recalled_events)} 条 · "
                        f"guides {len(hctx.active_guides)} 条 · 关系冷启动"
                    ),
                    node_id=node_id,
                    agent_id=agent.id,
                    recalled_count=len(hctx.recalled_events),
                    guides_count=len(hctx.active_guides),
                    persona_present=hctx.persona_perception is not None,
                    relationship_phase=(
                        hctx.relationship.current_phase if hctx.relationship else "none"
                    ),
                    top_recall_score=(
                        hctx.recalled_events[0].final_score
                        if hctx.recalled_events else None
                    ),
                ))
            except Exception as e:  # noqa: BLE001
                push(_event(
                    "harness_prompt_failed",
                    f"🧠 Harness · prompt 拼装失败,降级",
                    f"{type(e).__name__}: {str(e)[:160]}",
                    node_id=node_id,
                    agent_id=agent.id,
                ))

            # ---- 实际跑 LLM ----
            try:
                output = llm_gateway.run_agent(
                    agent_for_run,
                    user_msg,
                    history=None,
                    trace_hook=None,
                )
            except Exception as e:
                output = (
                    f"[{agent.name}] 执行失败(降级):\n"
                    f"错误: {type(e).__name__}: {str(e)[:200]}\n"
                    f"原任务: {state['user_input'][:120]}"
                )

            push(_event(
                "message_generated",
                f"{agent.name} 产出",
                f"第 {idx+1}/{len(agents)} 棒交付完毕",
                node_id=node_id,
                agent_id=agent.id,
                step=idx + 1,
                preview=output[:200],
            ))

            # ---- Harness Post-hook · 评分 + 三库联动 ----
            # 给 LLM 输出打 3 维度分,自动写入 event_memory(若达阈值),
            # 同时 bump persona interaction_count + apply relationship delta。
            try:
                post = post_hook_update_libraries(
                    agent_id=agent.id,
                    output=output,
                    workflow_id=workflow.id,
                    prior_context=(
                        state.get("triage_proposal", "")[:400]
                        + "\n"
                        + "\n".join(
                            f"{name}: {out[:200]}"
                            for name, out in prior_outputs[-2:]
                        )
                    )[:1500],
                )
                sc = post["score"]
                sensors_summary = post.get("sensors") or []
                sensor_brief = " · ".join(
                    f"{s['type']}={'✓' if s['passed'] else '✗'}{s['metric']:.2f}"
                    for s in sensors_summary
                ) or "(无 sensor)"
                push(_event(
                    "harness_post_hook",
                    f"🧠 Harness · {agent.name} 后处理",
                    (
                        f"评分 {sc['total_score']:.1f}/9 · "
                        f"{sc['emotion_tag']} · "
                        f"{'已写入' if post['wrote_event'] else '未达阈值'} · "
                        f"信任 Δ{post['trust_delta']:+.2f} → {post['trust_level']:.2f} · "
                        f"sensors {sensor_brief}"
                    ),
                    node_id=node_id,
                    agent_id=agent.id,
                    score=sc,
                    event_id=post["event_id"],
                    wrote_event=post["wrote_event"],
                    trust_delta=post["trust_delta"],
                    familiarity_delta=post["familiarity_delta"],
                    trust_level=post["trust_level"],
                    current_phase=post["current_phase"],
                    collaboration_count=post["collaboration_count"],
                    sensors=sensors_summary,
                    errors=post["errors"],
                ))
            except Exception as e:  # noqa: BLE001
                push(_event(
                    "harness_post_hook_failed",
                    f"🧠 Harness · 后处理异常",
                    f"{type(e).__name__}: {str(e)[:160]}",
                    node_id=node_id,
                    agent_id=agent.id,
                ))

            push(_event(
                "node_exited",
                f"{agent.name} 交棒",
                f"handoff → {'下一棒' if idx + 1 < len(agents) else 'CKO 蒸馏'}",
                node_id=node_id,
                agent_id=agent.id,
            ))
            return {
                "worker_outputs": prior_outputs + [(agent.name, output)],
            }

        return worker_node

    def distill_node(state: OPCState) -> OPCState:
        push(_event(
            "node_entered",
            "📚 CKO 四型闭环蒸馏",
            "项目交付完毕 · 五路径回写启动",
            node_id=DISTILL_NODE,
        ))
        outputs = list(state.get("worker_outputs", []) or [])
        try:
            prompt = build_distillation_prompt(
                user_input=state["user_input"],
                triage_proposal=state.get("triage_proposal", ""),
                all_outputs=outputs,
            )
            distillation = call_llm(prompt, temperature=0)
        except Exception:
            last = outputs[-1][1] if outputs else "(无产出)"
            distillation = build_fallback_response(workflow.name, last)

        # assistant_message 拼装:分诊 + 各岗位产出 + 蒸馏卡
        sections = []
        sections.append(f"## 🎯 分诊提案\n\n{state.get('triage_proposal', '')}")
        sections.append("---\n\n## 🚀 流水线交付")
        for i, (name, out) in enumerate(outputs, 1):
            sections.append(f"### {i}. {name}\n\n{out}")
        sections.append("---\n\n" + distillation)
        assistant_message = "\n\n".join(sections)

        push(_event(
            "node_exited",
            "📚 CKO 蒸馏完成",
            "五路径回写完成 · 项目闭环",
            node_id=DISTILL_NODE,
            preview=distillation[:200],
        ))
        return {
            "distillation": distillation,
            "assistant_message": assistant_message,
        }

    # ---------- 编图 ----------
    worker_nodes = [make_worker_node(i, a) for i, a in enumerate(agents)]
    use_distill = workflow.finalizer_enabled
    app = _compile_opc_app(
        workflow,
        agents,
        triage_node=triage_node,
        worker_nodes=worker_nodes,
        distill_node=distill_node if use_distill else None,
    )
    graph = workflow_graph_from_compiled(app)

    # ---------- 跑 ----------
    final_state = app.invoke({"user_input": user_input})

    if use_distill:
        assistant_message = str(final_state.get("assistant_message", "") or "")
    else:
        outputs = final_state.get("worker_outputs", []) or []
        if outputs:
            sections = [f"## 🎯 分诊提案\n\n{final_state.get('triage_proposal', '')}", "---\n\n## 🚀 流水线交付"]
            for i, (name, out) in enumerate(outputs, 1):
                sections.append(f"### {i}. {name}\n\n{out}")
            assistant_message = "\n\n".join(sections)
        else:
            assistant_message = "(无产出)"

    push(_event(
        "run_finished",
        "✓ 一人公司协作流完成",
        f"{len(agents)} 棒交付完毕 · " + ("含 CKO 五路径回写" if use_distill else "未启用 CKO 蒸馏"),
        workflow_id=workflow.id,
    ))

    artifacts = RunArtifacts(
        route_agent_id=agents[0].id,
        route_agent_name=agents[0].name,
        route_reason=f"一人公司协作流 · {len(agents)} 岗位接力",
        specialist_answer=None,
        final_answer=assistant_message,
    )
    return WorkflowRunResponse(
        workflow_id=workflow.id,
        user_input=user_input,
        assistant_message=assistant_message,
        trace=trace,
        graph=graph,
        artifacts=artifacts,
    )

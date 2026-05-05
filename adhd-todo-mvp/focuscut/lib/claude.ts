/**
 * Claude API 封装
 * 服务端调用，API Key 不暴露给前端
 */

import Anthropic from '@anthropic-ai/sdk';
import { EnergyLevel, DecomposeResponse } from '@/types';
import { buildSystemPrompt, USER_PROMPT_TEMPLATE } from './prompts';

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
  baseURL: process.env.ANTHROPIC_BASE_URL || undefined,
});

const CLAUDE_MODEL =
  process.env.CLAUDE_MODEL || 'claude-3-5-sonnet-20241022';

/**
 * 调用 Claude 拆解任务
 * @throws 如果 API Key 未配置或调用失败
 */
export async function decomposeTask(
  task: string,
  energyLevel: EnergyLevel
): Promise<DecomposeResponse> {
  if (!process.env.ANTHROPIC_API_KEY) {
    throw new Error('ANTHROPIC_API_KEY is not configured');
  }

  const response = await client.messages.create({
    model: CLAUDE_MODEL,
    max_tokens: 2048,
    system: buildSystemPrompt(energyLevel),
    messages: [
      { role: 'user', content: USER_PROMPT_TEMPLATE(task) },
    ],
  });

  // 提取文本内容
  const textBlock = response.content.find(b => b.type === 'text');
  if (!textBlock || textBlock.type !== 'text') {
    throw new Error('No text content in Claude response');
  }

  // 解析 JSON（容错：可能被 markdown code fence 包裹）
  let jsonStr = textBlock.text.trim();
  if (jsonStr.startsWith('```')) {
    jsonStr = jsonStr.replace(/^```(?:json)?\n?/, '').replace(/\n?```$/, '');
  }

  try {
    const parsed = JSON.parse(jsonStr) as DecomposeResponse;
    if (!parsed.subtasks || !Array.isArray(parsed.subtasks)) {
      throw new Error('Invalid response structure: missing subtasks array');
    }
    return parsed;
  } catch (e) {
    console.error('[claude] Failed to parse response:', jsonStr);
    throw new Error('Claude returned invalid JSON');
  }
}

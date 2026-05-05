import { NextRequest, NextResponse } from 'next/server';
import { decomposeTask } from '@/lib/claude';
import { DecomposeRequest } from '@/types';

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as DecomposeRequest;

    // 输入校验
    if (!body.task || typeof body.task !== 'string') {
      return NextResponse.json(
        { error: 'task is required and must be a string' },
        { status: 400 }
      );
    }

    if (body.task.length > 500) {
      return NextResponse.json(
        { error: 'task must be 500 characters or less' },
        { status: 400 }
      );
    }

    const validLevels = ['low', 'medium', 'high'];
    const energyLevel = validLevels.includes(body.energyLevel)
      ? body.energyLevel
      : 'medium';

    const result = await decomposeTask(body.task.trim(), energyLevel);

    return NextResponse.json(result);
  } catch (error: unknown) {
    const message =
      error instanceof Error ? error.message : 'Unknown error';
    console.error('[api/decompose]', message);

    return NextResponse.json(
      { error: 'Failed to decompose task. Please try again.' },
      { status: 500 }
    );
  }
}

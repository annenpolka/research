#!/usr/bin/env node

/**
 * Swarm Coordinator MCP Server
 *
 * Provides tools for multi-agent coordination:
 * - Messaging between agents
 * - Task queue management
 * - Swarm state queries
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { readFileSync, appendFileSync, existsSync, mkdirSync } from "fs";
import { join } from "path";

const SWARM_DIR = ".claude/swarm";

// Ensure swarm directory exists
if (!existsSync(SWARM_DIR)) {
  mkdirSync(SWARM_DIR, { recursive: true });
}

// Tool definitions
const tools = [
  {
    name: "swarm_send_message",
    description:
      "Send a message to another agent or broadcast to all agents in the swarm",
    inputSchema: {
      type: "object",
      properties: {
        recipient: {
          type: "string",
          description: "Agent ID to send to, or 'all' for broadcast",
        },
        subject: {
          type: "string",
          description: "Message subject (optional)",
        },
        body: {
          type: "string",
          description: "Message content",
        },
        priority: {
          type: "string",
          enum: ["low", "normal", "high"],
          default: "normal",
          description: "Message priority",
        },
      },
      required: ["recipient", "body"],
    },
  },
  {
    name: "swarm_get_messages",
    description: "Get messages sent to this agent",
    inputSchema: {
      type: "object",
      properties: {
        unread_only: {
          type: "boolean",
          default: true,
          description: "Only return unread messages",
        },
        limit: {
          type: "number",
          default: 20,
          description: "Maximum number of messages to return",
        },
      },
    },
  },
  {
    name: "swarm_claim_task",
    description:
      "Claim a task from the task queue. If task_id is omitted, auto-assigns the highest priority available task.",
    inputSchema: {
      type: "object",
      properties: {
        task_id: {
          type: "string",
          description: "Specific task ID to claim (optional)",
        },
      },
    },
  },
  {
    name: "swarm_complete_task",
    description: "Mark a task as completed",
    inputSchema: {
      type: "object",
      properties: {
        task_id: {
          type: "string",
          description: "Task ID to complete",
        },
        summary: {
          type: "string",
          description: "Completion summary",
        },
      },
      required: ["task_id"],
    },
  },
  {
    name: "swarm_get_state",
    description:
      "Query current swarm state: active agents, tasks, and file locks",
    inputSchema: {
      type: "object",
      properties: {
        query_type: {
          type: "string",
          enum: ["agents", "tasks", "locks", "all"],
          default: "all",
          description: "Type of state to query",
        },
      },
    },
  },
];

// Helper functions
function getAgentId(): string {
  const sessionFile = join(SWARM_DIR, ".session");
  if (existsSync(sessionFile)) {
    return readFileSync(sessionFile, "utf-8").trim();
  }
  return "unknown-agent";
}

function appendJsonl(filename: string, record: any) {
  const filepath = join(SWARM_DIR, filename);
  appendFileSync(filepath, JSON.stringify(record) + "\n");
}

function readJsonl(filename: string): any[] {
  const filepath = join(SWARM_DIR, filename);
  if (!existsSync(filepath)) {
    return [];
  }

  const content = readFileSync(filepath, "utf-8").trim();
  if (!content) {
    return [];
  }

  return content
    .split("\n")
    .filter((line) => line.trim())
    .map((line) => JSON.parse(line));
}

// Tool handlers
async function handleSendMessage(params: any) {
  const agentId = getAgentId();
  const { recipient, subject = "", body, priority = "normal" } = params;

  const message = {
    id: `msg-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
    from: agentId,
    to: recipient,
    subject,
    body,
    priority,
    timestamp: new Date().toISOString(),
    read: false,
  };

  appendJsonl("messages.jsonl", message);

  return {
    content: [
      {
        type: "text",
        text: `✓ Message sent to ${recipient}${subject ? ` (${subject})` : ""}`,
      },
    ],
  };
}

async function handleGetMessages(params: any) {
  const agentId = getAgentId();
  const { unread_only = true, limit = 20 } = params;

  const allMessages = readJsonl("messages.jsonl");

  const messages = allMessages
    .filter((msg) => msg.to === agentId || msg.to === "all")
    .filter((msg) => !unread_only || !msg.read)
    .slice(-limit)
    .reverse();

  if (messages.length === 0) {
    return {
      content: [
        {
          type: "text",
          text: "No messages.",
        },
      ],
    };
  }

  const formatted = messages
    .map(
      (msg) => `
**From**: ${msg.from}
**Subject**: ${msg.subject || "(no subject)"}
**Time**: ${new Date(msg.timestamp).toLocaleString()}
**Priority**: ${msg.priority}

${msg.body}

---
`
    )
    .join("\n");

  return {
    content: [
      {
        type: "text",
        text: `📬 ${messages.length} message(s):\n\n${formatted}`,
      },
    ],
  };
}

async function handleClaimTask(params: any) {
  const agentId = getAgentId();
  const { task_id } = params;

  const allTasks = readJsonl("tasks.jsonl");

  // Build current task state
  const taskState = new Map<string, any>();
  for (const record of allTasks) {
    if (record.id && !record.task_id) {
      // Task definition
      taskState.set(record.id, { ...record, status: "pending" });
    } else if (record.task_id) {
      // Task state update
      const task = taskState.get(record.task_id);
      if (task) {
        Object.assign(task, record);
      }
    }
  }

  // Find available tasks
  const availableTasks = Array.from(taskState.values()).filter(
    (t) => t.status === "pending" && !t.assigned_to
  );

  let taskToClaim;
  if (task_id) {
    taskToClaim = taskState.get(task_id);
    if (!taskToClaim || taskToClaim.status !== "pending") {
      return {
        content: [
          {
            type: "text",
            text: `❌ Task ${task_id} is not available`,
          },
        ],
      };
    }
  } else {
    // Auto-assign highest priority task
    if (availableTasks.length === 0) {
      return {
        content: [
          {
            type: "text",
            text: "No available tasks to claim",
          },
        ],
      };
    }

    availableTasks.sort((a, b) => (b.priority || 0) - (a.priority || 0));
    taskToClaim = availableTasks[0];
  }

  // Claim the task
  const claim = {
    task_id: taskToClaim.id,
    agent_id: agentId,
    claimed_at: new Date().toISOString(),
    status: "in_progress",
  };

  appendJsonl("tasks.jsonl", claim);

  return {
    content: [
      {
        type: "text",
        text: `✓ Claimed task **${taskToClaim.id}**: ${taskToClaim.description}

**Priority**: ${taskToClaim.priority || 0}
**Files**: ${taskToClaim.files?.join(", ") || "N/A"}
${taskToClaim.dependencies?.length ? `**Dependencies**: ${taskToClaim.dependencies.join(", ")}` : ""}

You can now work on this task. When complete, use \`swarm_complete_task\`.
`,
      },
    ],
  };
}

async function handleCompleteTask(params: any) {
  const agentId = getAgentId();
  const { task_id, summary = "" } = params;

  const completion = {
    task_id,
    agent_id: agentId,
    completed_at: new Date().toISOString(),
    status: "completed",
    summary,
  };

  appendJsonl("tasks.jsonl", completion);

  // Broadcast completion
  const message = {
    id: `msg-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
    from: agentId,
    to: "all",
    subject: `Task ${task_id} completed`,
    body: `Task **${task_id}** has been completed by ${agentId}.${summary ? `\n\nSummary: ${summary}` : ""}`,
    priority: "normal",
    timestamp: new Date().toISOString(),
    read: false,
  };

  appendJsonl("messages.jsonl", message);

  return {
    content: [
      {
        type: "text",
        text: `✓ Task ${task_id} marked as completed. Broadcast notification sent to all agents.`,
      },
    ],
  };
}

async function handleGetState(params: any) {
  const { query_type = "all" } = params;

  let result = "";

  if (query_type === "agents" || query_type === "all") {
    const agents = readJsonl("agents.jsonl");
    const activeAgents = new Map<string, any>();

    for (const record of agents) {
      if (record.id) {
        if (record.terminated_at) {
          activeAgents.delete(record.id);
        } else {
          activeAgents.set(record.id, record);
        }
      }
    }

    result += `## 🤖 Active Agents (${activeAgents.size})\n\n`;
    for (const agent of activeAgents.values()) {
      result += `- **${agent.id}** (started: ${new Date(agent.started_at).toLocaleString()})\n`;
    }
    result += "\n";
  }

  if (query_type === "tasks" || query_type === "all") {
    const allTasks = readJsonl("tasks.jsonl");
    const taskState = new Map<string, any>();

    for (const record of allTasks) {
      if (record.id && !record.task_id) {
        taskState.set(record.id, { ...record, status: "pending" });
      } else if (record.task_id) {
        const task = taskState.get(record.task_id);
        if (task) {
          Object.assign(task, record);
        }
      }
    }

    const byStatus = {
      pending: [] as any[],
      in_progress: [] as any[],
      completed: [] as any[],
    };

    for (const task of taskState.values()) {
      byStatus[task.status as keyof typeof byStatus]?.push(task);
    }

    result += `## 📋 Tasks\n\n`;
    result += `- Pending: ${byStatus.pending.length}\n`;
    result += `- In Progress: ${byStatus.in_progress.length}\n`;
    result += `- Completed: ${byStatus.completed.length}\n\n`;

    if (byStatus.in_progress.length > 0) {
      result += `**In Progress**:\n`;
      for (const task of byStatus.in_progress) {
        result += `- ${task.id} (by ${task.agent_id}): ${task.description}\n`;
      }
      result += "\n";
    }
  }

  if (query_type === "locks" || query_type === "all") {
    const locks = readJsonl("locks.jsonl");
    const activeLocks = new Map<string, any>();

    for (const record of locks) {
      if (record.status === "released") {
        activeLocks.delete(record.file_path);
      } else if (record.file_path && record.holder) {
        const expiresAt = new Date(record.expires_at);
        if (expiresAt > new Date()) {
          activeLocks.set(record.file_path, record);
        }
      }
    }

    result += `## 🔒 Active File Locks (${activeLocks.size})\n\n`;
    if (activeLocks.size > 0) {
      for (const lock of activeLocks.values()) {
        const remaining = Math.max(
          0,
          Math.floor(
            (new Date(lock.expires_at).getTime() - Date.now()) / 1000 / 60
          )
        );
        result += `- **${lock.file_path}**\n`;
        result += `  - Holder: ${lock.holder}\n`;
        result += `  - Reason: ${lock.reason}\n`;
        result += `  - Expires in: ${remaining} min\n`;
      }
    } else {
      result += "No active locks.\n";
    }
  }

  return {
    content: [
      {
        type: "text",
        text: result,
      },
    ],
  };
}

// Create server
const server = new Server(
  {
    name: "swarm-coordinator",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Register handlers
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: params } = request.params;

  try {
    switch (name) {
      case "swarm_send_message":
        return await handleSendMessage(params);
      case "swarm_get_messages":
        return await handleGetMessages(params);
      case "swarm_claim_task":
        return await handleClaimTask(params);
      case "swarm_complete_task":
        return await handleCompleteTask(params);
      case "swarm_get_state":
        return await handleGetState(params);
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: `Error: ${error instanceof Error ? error.message : String(error)}`,
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Swarm Coordinator MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});

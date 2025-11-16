import { Hono } from "npm:hono";
import { cors } from "npm:hono/cors";
import { logger } from "npm:hono/logger";
import * as kv from "./kv_store.tsx";
const app = new Hono();

// Enable logger
app.use('*', logger(console.log));

// Enable CORS for all routes and methods
app.use(
  "/*",
  cors({
    origin: "*",
    allowHeaders: ["Content-Type", "Authorization"],
    allowMethods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    exposeHeaders: ["Content-Length"],
    maxAge: 600,
  }),
);

// Health check endpoint
app.get("/make-server-3ecf4837/health", (c) => {
  return c.json({ status: "ok" });
});

// AI Meeting Analysis endpoint
app.post("/make-server-3ecf4837/analyze-meeting", async (c) => {
  try {
    const { content, meetingTitle } = await c.req.json();
    
    if (!content) {
      return c.json({ error: "회의 내용이 필요합니다." }, 400);
    }

    const apiKey = Deno.env.get("OPENAI_API_KEY");
    if (!apiKey) {
      console.error("OpenAI API key not configured");
      return c.json({ error: "API 키가 설정되지 않았습니다." }, 500);
    }

    console.log("API key found, length:", apiKey.length);
    console.log("API key starts with:", apiKey.substring(0, 7));

    const systemPrompt = `당신은 회의록 분석 전문가입니다. 회의 내용을 분석하여 다음을 JSON 형식으로 추출해주세요:

1. summary: 회의 내용의 핵심 요약 (2-3문장)
2. actionItems: 액션 아이템 배열, 각각:
   - task: 할 일 (구체적으로)
   - assignee: 담당자 (언급된 경우, 없으면 "미정")
   - dueDate: 마감일, 회의 시작일을 기준으로 회의에서 언급된 날짜 파악 (없으면 "미정")
   - priority: "높음", "중간", "낮음" 중 하나로 설정, 긴급도(마감일 기준)와 중요도(회의 주제에 대한 중요도)에 따라 판단 긴급하고 중요한 일은 높음, 긴급하지 않고 중요하지 않은 일은 낮음, 그 외는 중간
3. participants: 참석자 이름 배열
4. keyDecisions: 주요 결정사항 배열
5. nextSteps: 다음 진행 단계 배열 priority를 기반으로 근거 설명

JSON만 반환하고 다른 텍스트는 포함하지 마세요.`;

    const userPrompt = `다음 회의 내용을 분석해주세요:\n\n회의 제목: ${meetingTitle || "제목 없음"}\n\n회의 내용:\n${content}`;

    console.log("Calling OpenAI API for meeting analysis...");
    console.log("Meeting content length:", content.length);
    
    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: userPrompt }
        ],
        temperature: 0.7,
        response_format: { type: "json_object" }
      }),
    });

    if (!response.ok) {
      const errorData = await response.text();
      console.error(`OpenAI API error: ${response.status} - ${errorData}`);
      console.error("Full error response:", errorData);
      return c.json({ 
        error: `OpenAI API 오류 (${response.status}): ${response.statusText}`,
        details: errorData.substring(0, 200)
      }, response.status);
    }

    const data = await response.json();
    const analysisResult = JSON.parse(data.choices[0].message.content);
    
    console.log("Analysis completed successfully");
    return c.json(analysisResult);

  } catch (error) {
    console.error("Error in analyze-meeting endpoint:", error);
    return c.json({ 
      error: `회의 분석 중 오류 발생: ${error instanceof Error ? error.message : "알 수 없는 오류"}` 
    }, 500);
  }
});

Deno.serve(app.fetch);
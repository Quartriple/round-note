import { useState, useEffect } from "react";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Card } from "@/shared/ui/card";
import { ArrowLeft, Plus, X, Save, RotateCcw, Tag } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/shared/ui/badge";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/shared/ui/select";

interface KeywordSettingsProps {
  onBack: () => void;
}

interface DomainSetting {
  domain: string;
  keywords: string[];
}

const STORAGE_KEY = "roundnote-llm-context-settings";

const DEFAULT_SETTINGS: DomainSetting = {
  domain: "일반",
  keywords: [
  ],
};

export function KeywordSettings({ onBack }: KeywordSettingsProps) {
  const [domain, setDomain] = useState<string>(DEFAULT_SETTINGS.domain);
  const [keywords, setKeywords] = useState<string[]>(DEFAULT_SETTINGS.keywords);
  const [newKeyword, setNewKeyword] = useState<string>("");
  const [isEditing, setIsEditing] = useState(false);

  // ✅ 로컬 스토리지 불러오기
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed: DomainSetting = JSON.parse(saved);
        if (parsed.domain) setDomain(parsed.domain);
        if (parsed.keywords) setKeywords(parsed.keywords);
      } catch (error) {
        console.error("저장된 LLM 설정 로드 실패:", error);
      }
    }
  }, []);

  // ✅ 저장
  const saveSettings = () => {
    const settingsToSave: DomainSetting = { domain, keywords };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settingsToSave));
    toast.success("분야 및 용어 설정이 저장되었습니다.");
    setIsEditing(false);
  };

  // ✅ 초기화
  const resetToDefaults = () => {
    setDomain(DEFAULT_SETTINGS.domain);
    setKeywords(DEFAULT_SETTINGS.keywords);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_SETTINGS));
    toast.success("기본 설정으로 복원되었습니다.");
    setIsEditing(false);
  };

  // ✅ 용어 추가
  const addKeyword = () => {
    const keyword = newKeyword.trim();
    if (!keyword) {
      toast.error("용어를 입력해주세요.");
      return;
    }
    if (keywords.includes(keyword)) {
      toast.error("이미 존재하는 용어입니다.");
      return;
    }
    setKeywords([...keywords, keyword]);
    setNewKeyword("");
    setIsEditing(true);
  };

  // ✅ 용어 삭제
  const removeKeyword = (keyword: string) => {
    setKeywords(keywords.filter((k) => k !== keyword));
    setIsEditing(true);
  };

  return (
    <div className="bg-white rounded-2xl p-8 shadow-sm border border-border w-[1100px] max-w-[1100px] mx-auto">
      {/* 헤더 */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            onClick={onBack}
            variant="ghost"
            size="icon"
            className="hover:bg-muted"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h2 className="text-foreground">분야 및 용어 설정</h2>
            <p className="text-muted-foreground text-sm mt-1">
              LLM이 회의 내용을 더 정확히 이해하도록 분야와 관련 용어를 지정하세요.
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          {isEditing && (
            <Button
              onClick={saveSettings}
              size="sm"
              className="gap-2 bg-primary hover:bg-primary/90"
            >
              <Save className="w-4 h-4" />
              저장
            </Button>
          )}
          <Button
            onClick={resetToDefaults}
            size="sm"
            variant="outline"
            className="gap-2"
          >
            <RotateCcw className="w-4 h-4" />
            초기화
          </Button>
        </div>
      </div>

      {/* ✅ 분야 선택 */}
      <div className="mb-8">
        <Label className="text-sm font-semibold mb-2 block">분야 선택</Label>
        <Select
          value={domain}
          onValueChange={(v) => {
            setDomain(v);
            setIsEditing(true);
          }}
        >
          <SelectTrigger className="w-[250px]">
            <SelectValue placeholder="회의 분야 선택" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="일반">일반</SelectItem>
            <SelectItem value="기술개발">기술개발</SelectItem>
            <SelectItem value="마케팅">마케팅</SelectItem>
            <SelectItem value="디자인">디자인</SelectItem>
            <SelectItem value="경영전략">경영전략</SelectItem>
            <SelectItem value="프로덕트기획">프로덕트 기획</SelectItem>
            <SelectItem value="교육훈련">교육훈련</SelectItem>
          </SelectContent>
        </Select>
        <p className="text-sm text-muted-foreground mt-1">
          선택한 분야는 회의 요약 및 분석 시 LLM이 참고하는 컨텍스트로 전달됩니다.
        </p>
      </div>

      {/* ✅ 용어 리스트 */}
      <Card className="p-6 border-2 rounded-xl border-border">
        <div className="mb-4 flex items-center gap-2">
          <Tag className="w-5 h-5 text-primary" />
          <Label className="text-base">관련 용어</Label>
          <Badge variant="secondary" className="ml-2">
            {keywords.length}개
          </Badge>
        </div>

        {/* 용어 표시 */}
        <div className="flex flex-wrap gap-2 mb-4">
          {keywords.map((keyword) => (
            <Badge
              key={keyword}
              variant="outline"
              className="pl-3 pr-2 py-1.5 text-sm hover:bg-red-50 hover:border-red-300 transition-colors"
            >
              {keyword}
              <button
                onClick={() => removeKeyword(keyword)}
                className="ml-2 hover:text-red-600 transition-colors"
              >
                <X className="w-3 h-3" />
              </button>
            </Badge>
          ))}
        </div>

        {/* 새 용어 추가 */}
        <div className="flex gap-2">
          <Input
            placeholder="새 용어 추가"
            value={newKeyword}
            onChange={(e) => setNewKeyword(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === "Enter") addKeyword();
            }}
            className="flex-1"
          />
          <Button
            onClick={addKeyword}
            size="sm"
            variant="outline"
            className="gap-2"
          >
            <Plus className="w-4 h-4" />
            추가
          </Button>
        </div>
      </Card>

      {/* 안내 */}
      <div className="p-4 bg-primary/5 border border-primary/20 rounded-xl mt-6">
        <h4 className="text-sm text-primary mb-2">도움말</h4>
        <ul className="space-y-1 text-sm text-blue-700">
          <li>• 분야와 관련 용어는 LLM 회의 요약 및 분석에 직접 반영됩니다.</li>
          <li>• 특정 용어를 추가하면 그 주제에 더 민감하게 반응합니다.</li>
          <li>• 예: “마케팅” 분야에 “ROI, 캠페인, 타깃층”을 추가하면 관련 토픽에 집중합니다.</li>
          <li>• 변경 후 저장 버튼을 눌러야 적용됩니다.</li>
        </ul>
      </div>
    </div>
  );
}

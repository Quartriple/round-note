import { useState, useEffect } from "react";
import { Button } from "@/shared/ui/button";
import { Label } from "@/shared/ui/label";
import { Card } from "@/shared/ui/card";
import { ArrowLeft, Languages, CheckCircle2, Globe } from "lucide-react";
import { toast } from "sonner";
import { RadioGroup, RadioGroupItem } from "@/shared/ui/radio-group";

interface TranslationSettingsProps {
  onBack: () => void;
}

interface TranslationConfig {
  language: "ko" | "en";
  autoTranslate: boolean;
}

const STORAGE_KEY = "roundnote-translation-settings";

export function TranslationSettings({ onBack }: TranslationSettingsProps) {
  const [translationConfig, setTranslationConfig] = useState<TranslationConfig>({
    language: "ko",
    autoTranslate: false,
  });

  useEffect(() => {
    // Load saved settings
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        setTranslationConfig(JSON.parse(saved));
      } catch (error) {
        console.error("Failed to load translation settings:", error);
      }
    }
  }, []);

  const saveSettings = (config: TranslationConfig) => {
    setTranslationConfig(config);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
    toast.success("번역 설정이 저장되었습니다");
  };

  const handleLanguageChange = (language: "ko" | "en") => {
    saveSettings({ ...translationConfig, language });
  };

  return (
    <div className="bg-white rounded-2xl p-8 shadow-sm border border-border">
      <div className="mb-6 flex items-center gap-4">
        <Button
          onClick={onBack}
          variant="ghost"
          size="icon"
          className="hover:bg-muted"
        >
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div>
          <h2 className="text-foreground">번역 설정</h2>
          <p className="text-muted-foreground text-sm mt-1">
            음성 인식 및 번역 언어를 설정합니다
          </p>
        </div>
      </div>

      <div className="space-y-6">
        {/* Language Selection */}
        <Card className="p-6 border-2 rounded-xl border-border">
          <div className="flex items-start gap-3 mb-4">
            <Languages className="w-6 h-6 text-primary mt-1" />
            <div className="flex-1">
              <Label className="text-base">음성 인식 언어</Label>
              <p className="text-sm text-muted-foreground mt-1">
                회의 중 사용할 음성 인식 언어를 선택하세요
              </p>
            </div>
          </div>

          <RadioGroup
            value={translationConfig.language}
            onValueChange={(value) => handleLanguageChange(value as "ko" | "en")}
            className="space-y-3 mt-4"
          >
            <Card className={`p-4 border-2 rounded-xl cursor-pointer transition-all hover:border-primary/40 ${
              translationConfig.language === "ko" ? "border-primary bg-primary/5" : "border-border"
            }`}>
              <div className="flex items-start gap-3">
                <RadioGroupItem value="ko" id="ko" className="mt-1" />
                <Label htmlFor="ko" className="flex-1 cursor-pointer">
                  <div className="flex items-center gap-2 mb-1">
                  
                    <span>한국어</span>
                    {translationConfig.language === "ko" && (
                      <CheckCircle2 className="w-4 h-4 text-primary ml-auto" />
                    )}
                  </div>
                  
                </Label>
              </div>
            </Card>

            <Card className={`p-4 border-2 rounded-xl cursor-pointer transition-all hover:border-primary/40 ${
              translationConfig.language === "en" ? "border-primary bg-primary/5" : "border-border"
            }`}>
              <div className="flex items-start gap-3">
                <RadioGroupItem value="en" id="en" className="mt-1" />
                <Label htmlFor="en" className="flex-1 cursor-pointer">
                  <div className="flex items-center gap-2 mb-1">
                    <span>English</span>
                    {translationConfig.language === "en" && (
                      <CheckCircle2 className="w-4 h-4 text-primary ml-auto" />
                    )}
                  </div>
                </Label>
              </div>
            </Card>
          </RadioGroup>
        </Card>

        {/* Current Setting Display */}
        <Card className="p-6 bg-green-50 border-green-200 rounded-xl">
          <div className="flex items-start gap-3">
            <Globe className="w-5 h-5 text-green-600 mt-0.5" />
            <div>
              <Label className="text-base text-green-900">현재 설정</Label>
              <p className="text-sm text-green-700 mt-1">
                {translationConfig.language === "ko" 
                  ? "한국어 음성 인식이 활성화되어 있습니다" 
                  : "English speech recognition is enabled"}
              </p>
            </div>
          </div>
        </Card>

        {/* Language Info */}
        <div className="space-y-4">
          <h3 className="text-foreground">언어별 기능</h3>
          
          <Card className="p-4 border border-border rounded-xl">
            <div className="flex items-start gap-3">
              <span className="text-xl">🇰🇷</span>
              <div>
                <Label className="text-sm">한국어 (Korean)</Label>
                <ul className="text-sm text-muted-foreground mt-2 space-y-1">
                  <li>• Web Speech API를 사용한 실시간 한국어 음성 인식</li>
                  <li>• 한국어 회의록 자동 생성</li>
                  <li>• 한국어 액션 아이템 추출</li>
                </ul>
              </div>
            </div>
          </Card>

          <Card className="p-4 border border-border rounded-xl">
            <div className="flex items-start gap-3">
              <span className="text-xl">🇺🇸</span>
              <div>
                <Label className="text-sm">English</Label>
                <ul className="text-sm text-muted-foreground mt-2 space-y-1">
                  <li>• Real-time English speech recognition using Web Speech API</li>
                  <li>• Automatic meeting minutes generation in English</li>
                  <li>• English action item extraction</li>
                </ul>
              </div>
            </div>
          </Card>
        </div>

        {/* Info */}
        <div className="p-4 bg-muted border border-border rounded-xl">
          <h4 className="text-sm text-foreground mb-2">설정 안내</h4>
          <ul className="space-y-1 text-sm text-muted-foreground">
            <li>• 설정한 언어는 회의 시작 시 자동으로 적용됩니다</li>
            <li>• 회의 중에도 언어를 변경할 수 있습니다</li>
            <li>• 브라우저가 선택한 언어를 지원해야 합니다</li>
            <li>• Chrome 브라우저에서 가장 정확한 인식률을 제공합니다</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

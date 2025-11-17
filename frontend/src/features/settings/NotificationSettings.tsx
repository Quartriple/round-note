import { useState, useEffect } from "react";
import { Button } from "@/shared/ui/button";
import { Switch } from "@/shared/ui/switch";
import { Label } from "@/shared/ui/label";
import { Card } from "@/shared/ui/card";
import { ArrowLeft, Bell, Calendar, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";

interface NotificationSettingsProps {
  onBack: () => void;
}

interface NotificationConfig {
  enabled: boolean;
  sevenDays: boolean;
  threeDays: boolean;
  oneDay: boolean;
}

const STORAGE_KEY = "roundnote-notification-settings";

export function NotificationSettings({ onBack }: NotificationSettingsProps) {
  const [notificationConfig, setNotificationConfig] = useState<NotificationConfig>({
    enabled: false,
    sevenDays: false,
    threeDays: false,
    oneDay: false,
  });
  const [permissionGranted, setPermissionGranted] = useState(false);

  useEffect(() => {
    // Load saved settings
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        setNotificationConfig(JSON.parse(saved));
      } catch (error) {
        console.error("Failed to load notification settings:", error);
      }
    }

    // Check notification permission
    if ("Notification" in window) {
      setPermissionGranted(Notification.permission === "granted");
    }
  }, []);

  const saveSettings = (config: NotificationConfig) => {
    setNotificationConfig(config);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
    toast.success("알림 설정이 저장되었습니다");
  };

  const requestNotificationPermission = async () => {
    if (!("Notification" in window)) {
      toast.error("이 브라우저는 알림을 지원하지 않습니다");
      return;
    }

    try {
      const permission = await Notification.requestPermission();
      if (permission === "granted") {
        setPermissionGranted(true);
        toast.success("알림 권한이 허용되었습니다");
        
        // Send test notification
        new Notification("RoundNote 알림 테스트", {
          body: "알림이 정상적으로 설정되었습니다!",
          icon: "/favicon.ico",
        });
      } else {
        toast.error("알림 권한이 거부되었습니다");
      }
    } catch (error) {
      console.error("Failed to request notification permission:", error);
      toast.error("알림 권한 요청 중 오류가 발생했습니다");
    }
  };

  const handleToggleEnabled = (enabled: boolean) => {
    if (enabled && !permissionGranted) {
      requestNotificationPermission();
    }
    saveSettings({ ...notificationConfig, enabled });
  };

  const handleToggleNotification = (type: "sevenDays" | "threeDays" | "oneDay", value: boolean) => {
    saveSettings({ ...notificationConfig, [type]: value });
  };

  const sendTestNotification = () => {
    if (!permissionGranted) {
      toast.error("먼저 알림 권한을 허용해주세요");
      return;
    }

    new Notification("RoundNote 알림 테스트", {
      body: "회의 액션아이템 마감일이 3일 남았습니다",
      icon: "/favicon.ico",
    });
    toast.success("테스트 알림이 전송되었습니다");
  };

  return (
    <div className="bg-white rounded-xl p-8 shadow-lg border border-slate-200">
      <div className="mb-6 flex items-center gap-4">
        <Button
          onClick={onBack}
          variant="ghost"
          size="icon"
          className="hover:bg-slate-100"
        >
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div>
          <h2 className="text-primary">액션아이템 알림 설정</h2>
          <p className="text-muted-foreground text-sm mt-1">
            마감일이 다가오면 알림을 받을 수 있습니다
          </p>
        </div>
      </div>

      <div className="space-y-6">
        {/* Main Toggle */}
        <Card className="p-6 border-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Bell className="w-6 h-6 text-primary" />
              <div>
                <Label className="text-base">알림 활성화</Label>
                <p className="text-sm text-muted-foreground mt-1">
                  액션아이템 마감일 알림을 받습니다
                </p>
              </div>
            </div>
            <Switch
              checked={notificationConfig.enabled}
              onCheckedChange={handleToggleEnabled}
            />
          </div>

          {!permissionGranted && (
            <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
              <p className="text-sm text-amber-800 mb-2">
                알림을 받으려면 브라우저 알림 권한이 필요합니다
              </p>
              <Button
                onClick={requestNotificationPermission}
                size="sm"
                variant="outline"
                className="border-amber-300 hover:bg-amber-100"
              >
                알림 권한 허용하기
              </Button>
            </div>
          )}
        </Card>

        {/* Notification Options */}
        <div className="space-y-4">
          <h3 className="text-slate-700 flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            알림 시점 설정
          </h3>

          <Card className="p-6 border">
            <div className="flex items-center justify-between mb-4">
              <div>
                <Label className="text-base">7일 전 알림</Label>
                <p className="text-sm text-muted-foreground mt-1">
                  마감일 7일 전에 알림을 받습니다
                </p>
              </div>
              <Switch
                checked={notificationConfig.sevenDays}
                onCheckedChange={(value) => handleToggleNotification("sevenDays", value)}
                disabled={!notificationConfig.enabled}
              />
            </div>
          </Card>

          <Card className="p-6 border">
            <div className="flex items-center justify-between mb-4">
              <div>
                <Label className="text-base">3일 전 알림</Label>
                <p className="text-sm text-muted-foreground mt-1">
                  마감일 3일 전에 알림을 받습니다
                </p>
              </div>
              <Switch
                checked={notificationConfig.threeDays}
                onCheckedChange={(value) => handleToggleNotification("threeDays", value)}
                disabled={!notificationConfig.enabled}
              />
            </div>
          </Card>

          <Card className="p-6 border">
            <div className="flex items-center justify-between mb-4">
              <div>
                <Label className="text-base">1일 전 알림</Label>
                <p className="text-sm text-muted-foreground mt-1">
                  마감일 1일 전에 알림을 받습니다
                </p>
              </div>
              <Switch
                checked={notificationConfig.oneDay}
                onCheckedChange={(value) => handleToggleNotification("oneDay", value)}
                disabled={!notificationConfig.enabled}
              />
            </div>
          </Card>
        </div>

        {/* Test Button */}
        {permissionGranted && notificationConfig.enabled && (
          <Card className="p-6 bg-blue-50 border-blue-200">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 text-blue-600 mt-0.5" />
              <div className="flex-1">
                <Label className="text-base text-blue-900">알림 테스트</Label>
                <p className="text-sm text-blue-700 mt-1 mb-3">
                  알림이 정상적으로 작동하는지 테스트해보세요
                </p>
                <Button
                  onClick={sendTestNotification}
                  size="sm"
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  테스트 알림 보내기
                </Button>
              </div>
            </div>
          </Card>
        )}

        {/* Info */}
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
          <h4 className="text-sm font-semibold text-slate-700 mb-2">알림 동작 방식</h4>
          <ul className="space-y-1 text-sm text-slate-600">
            <li>• 설정한 시점에 브라우저 알림이 표시됩니다</li>
            <li>• 여러 액션아이템이 있는 경우 각각 알림이 발송됩니다</li>
            <li>• 알림은 매일 자정에 확인됩니다</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

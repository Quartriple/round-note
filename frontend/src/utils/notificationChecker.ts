import { Meeting, ActionItem } from "../features/dashboard/Dashboard";

interface NotificationConfig {
  enabled: boolean;
  sevenDays: boolean;
  threeDays: boolean;
  oneDay: boolean;
}

const STORAGE_KEY = "roundnote-notification-settings";
const LAST_CHECK_KEY = "roundnote-last-notification-check";

// Get days until due date
function getDaysUntilDue(dueDate: string): number {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  
  const due = new Date(dueDate);
  due.setHours(0, 0, 0, 0);
  
  const diffTime = due.getTime() - now.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  return diffDays;
}

// Check if notification should be sent for this action item
function shouldNotify(
  actionItem: ActionItem,
  config: NotificationConfig,
  lastCheckDate: string
): { notify: boolean; daysLeft: number } {
  if (!config.enabled || actionItem.completed) {
    return { notify: false, daysLeft: 0 };
  }

  const daysLeft = getDaysUntilDue(actionItem.dueDate);
  
  // Check if we already notified today
  const today = new Date().toDateString();
  if (lastCheckDate === today) {
    return { notify: false, daysLeft };
  }

  // Check notification thresholds
  if (config.sevenDays && daysLeft === 7) {
    return { notify: true, daysLeft: 7 };
  }
  if (config.threeDays && daysLeft === 3) {
    return { notify: true, daysLeft: 3 };
  }
  if (config.oneDay && daysLeft === 1) {
    return { notify: true, daysLeft: 1 };
  }

  return { notify: false, daysLeft };
}

// Send browser notification
function sendNotification(
  meetingTitle: string,
  actionItem: ActionItem,
  daysLeft: number
) {
  if (!("Notification" in window) || Notification.permission !== "granted") {
    return;
  }

  const title = "RoundNote 알림";
  const body = `"${meetingTitle}" 회의\n액션아이템 "${actionItem.text}" 마감일이 ${daysLeft}일 남았습니다`;
  
  new Notification(title, {
    body,
    icon: "/favicon.ico",
    tag: `action-item-${actionItem.id}`,
  });
}

// Main notification checker
export function checkNotifications(meetings: Meeting[]) {
  // Get notification config
  const configStr = localStorage.getItem(STORAGE_KEY);
  if (!configStr) return;

  let config: NotificationConfig;
  try {
    config = JSON.parse(configStr);
  } catch {
    return;
  }

  if (!config.enabled) return;

  // Get last check date
  const lastCheckDate = localStorage.getItem(LAST_CHECK_KEY) || "";

  // Check all action items
  let notificationsSent = 0;
  
  meetings.forEach((meeting) => {
    meeting.actionItems.forEach((actionItem) => {
      const { notify, daysLeft } = shouldNotify(actionItem, config, lastCheckDate);
      
      if (notify) {
        sendNotification(meeting.title, actionItem, daysLeft);
        notificationsSent++;
      }
    });
  });

  // Update last check date if notifications were sent
  if (notificationsSent > 0) {
    const today = new Date().toDateString();
    localStorage.setItem(LAST_CHECK_KEY, today);
  }

  return notificationsSent;
}

// Initialize notification checker - run on app startup and periodically
export function initNotificationChecker(meetings: Meeting[]) {
  // Check immediately
  checkNotifications(meetings);

  // Check every hour
  const intervalId = setInterval(() => {
    checkNotifications(meetings);
  }, 60 * 60 * 1000); // 1 hour

  return () => clearInterval(intervalId);
}

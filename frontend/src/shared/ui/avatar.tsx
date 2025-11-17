"use client";

import * as React from "react";
import * as AvatarPrimitive from "@radix-ui/react-avatar";
import { cn } from "./utils";

interface AvatarProps extends React.ComponentProps<typeof AvatarPrimitive.Root> {
  name?: string;          // 이름 (Fallback용)
  src?: string;           // 아바타 이미지 URL
  size?: number;          // 아바타 크기 (픽셀)
}

function Avatar({ name, src, size = 40, className, ...props }: AvatarProps) {
  const sizeClass = `w-[${size}px] h-[${size}px]`;

  return (
    <AvatarPrimitive.Root
      data-slot="avatar"
      className={cn(
        `relative flex shrink-0 overflow-hidden rounded-full ${sizeClass}`,
        className
      )}
      {...props}
    >
      {src ? (
        <AvatarPrimitive.Image
          src={src}
          alt={name}
          className="aspect-square w-full h-full object-cover"
        />
      ) : (
        <AvatarPrimitive.Fallback className="bg-muted flex items-center justify-center w-full h-full rounded-full text-white font-medium">
          {name?.[0] ?? "?"}
        </AvatarPrimitive.Fallback>
      )}
    </AvatarPrimitive.Root>
  );
}

export { Avatar };
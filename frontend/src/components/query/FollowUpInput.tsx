"use client";

import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";

interface FollowUpInputProps {
  onSubmit: (query: string) => void;
  disabled?: boolean;
}

export function FollowUpInput({ onSubmit, disabled }: FollowUpInputProps) {
  const [value, setValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!value.trim() || disabled) return;
    onSubmit(value.trim());
    setValue("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      if (!value.trim() || disabled) return;
      onSubmit(value.trim());
      setValue("");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2">
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask a follow-up question..."
        disabled={disabled}
        className="flex-1 rounded-md border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
      />
      <Button type="submit" size="sm" disabled={!value.trim() || disabled}>
        Ask
      </Button>
    </form>
  );
}

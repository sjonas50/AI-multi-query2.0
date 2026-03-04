"use client";

import { Skeleton } from "@/components/ui/skeleton";

interface SuggestedQuestionsProps {
  questions: string[];
  loading?: boolean;
  onSelect: (question: string) => void;
}

export function SuggestedQuestions({ questions, loading, onSelect }: SuggestedQuestionsProps) {
  if (!loading && questions.length === 0) return null;

  return (
    <div className="space-y-2">
      <p className="text-xs font-medium text-muted-foreground">Suggested follow-ups</p>
      <div className="flex flex-wrap gap-2">
        {loading ? (
          <>
            <Skeleton className="h-8 w-48 rounded-full" />
            <Skeleton className="h-8 w-56 rounded-full" />
            <Skeleton className="h-8 w-40 rounded-full" />
          </>
        ) : (
          questions.map((q, i) => (
            <button
              key={i}
              type="button"
              onClick={() => onSelect(q)}
              className="rounded-full border bg-background px-3 py-1.5 text-sm text-foreground hover:bg-muted transition-colors animate-in fade-in duration-300"
              style={{ animationDelay: `${i * 75}ms` }}
            >
              {q}
            </button>
          ))
        )}
      </div>
    </div>
  );
}

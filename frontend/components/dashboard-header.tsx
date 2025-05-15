import { LucideSettings } from "lucide-react";

export function DashboardHeader() {
  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-16 items-center px-6">
        <div className="flex items-center gap-2 font-semibold">
          <LucideSettings className="h-5 w-5" />
          <span>Dashboard</span>
        </div>
        <div className="ml-auto flex items-center space-x-4">
          <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
            <span className="text-xs font-semibold text-primary">JD</span>
          </div>
        </div>
      </div>
    </header>
  );
}
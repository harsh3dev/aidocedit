import { DashboardForm } from "@/components/dashboard-form";
import { DashboardHeader } from "@/components/dashboard-header";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <DashboardHeader />
      <main className="flex-1">
        <div className="container mx-auto py-8 px-4 md:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl">
            <div className="mb-8 space-y-2">
              <h1 className="text-3xl font-bold tracking-tight">Query Dashboard</h1>
              <p className="text-muted-foreground">
                Enter your query and select a template to get started.
              </p>
            </div>
            <div className="rounded-lg border bg-card p-6 shadow-sm transition-all duration-200 hover:shadow-md">
              <DashboardForm />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
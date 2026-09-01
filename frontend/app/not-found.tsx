import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#05050A] px-4 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#DC143C] text-2xl font-bold text-white shadow-lg">
        SA
      </div>

      <h1 className="mt-6 text-4xl font-bold text-white">Page not found</h1>
      <p className="mt-3 max-w-md text-lg text-[#8A8A94]">
        The page you&apos;re looking for doesn&apos;t exist or has been moved.
      </p>

      <div className="mt-8 flex gap-3">
        <Link href="/">
          <Button size="lg">Go to homepage</Button>
        </Link>
        <Link href="/dashboard">
          <Button variant="outline" size="lg">Go to dashboard</Button>
        </Link>
      </div>
    </div>
  );
}

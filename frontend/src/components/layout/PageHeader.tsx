import React from 'react';

interface PageHeaderProps {
  title: string;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
}

export function PageHeader({ title, subtitle, actions }: PageHeaderProps) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-3 mb-6">
      <div className="flex-shrink-0">
        <h1 className="text-2xl font-semibold text-text-primary tracking-tight">{title}</h1>
        {subtitle && <p className="text-text-secondary text-sm mt-0.5">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-shrink-0 max-w-full flex-wrap gap-2 items-center">{actions}</div>}
    </div>
  );
}

/** Thin vertical divider between toolbar groups. */
export function ToolbarDivider() {
  return <div className="hidden sm:block w-px h-6 bg-border mx-1" />;
}

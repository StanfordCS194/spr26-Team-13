import type { CSSProperties, MouseEvent, ReactNode } from 'react';
import { Icon, type IconName } from './Icon';

type Variant = 'primary' | 'ghost' | 'surface' | 'dark';
type Size = 'lg' | 'md' | 'sm';

interface ButtonProps {
  children: ReactNode;
  onClick?: (e: MouseEvent<HTMLButtonElement>) => void;
  variant?: Variant;
  size?: Size;
  icon?: IconName;
  iconRight?: IconName;
  style?: CSSProperties;
  disabled?: boolean;
}

export function Button({
  children,
  onClick,
  variant = 'primary',
  size = 'lg',
  icon,
  iconRight,
  style,
  disabled,
}: ButtonProps) {
  const sizes: Record<Size, { height: number; padding: string; fontSize: number }> = {
    lg: { height: 56, padding: '0 24px', fontSize: 16 },
    md: { height: 44, padding: '0 18px', fontSize: 14 },
    sm: { height: 32, padding: '0 14px', fontSize: 13 },
  };
  const variants: Record<Variant, CSSProperties> = {
    primary: { background: 'var(--accent)', color: 'var(--on-accent)', border: 'none' },
    ghost: { background: 'transparent', color: 'var(--text-1)', border: '1px solid var(--hairline-2)' },
    surface: { background: 'var(--surface-2)', color: 'var(--text-1)', border: '1px solid var(--hairline)' },
    dark: { background: 'var(--surface-3)', color: 'var(--text-1)', border: '1px solid var(--hairline-2)' },
  };
  const s = sizes[size];
  const v = variants[variant];
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="press"
      style={{
        ...s,
        ...v,
        borderRadius: 9999,
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        fontFamily: 'var(--font-sans)',
        fontWeight: 600,
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        ...style,
      }}
    >
      {icon && <Icon name={icon} size={size === 'sm' ? 16 : 18} />}
      <span>{children}</span>
      {iconRight && <Icon name={iconRight} size={size === 'sm' ? 16 : 18} />}
    </button>
  );
}

interface AvatarProps {
  firstName: string;
  lastName: string;
  memberId: string;
  size?: number;
}

function hashCode(s: string): number {
  let hash = 0;
  for (let i = 0; i < s.length; i++) {
    hash = ((hash << 5) - hash) + s.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

function hslColor(memberId: string): string {
  const h = hashCode(memberId) % 360;
  return `hsl(${h}, 55%, 45%)`;
}

export function Avatar({ firstName, lastName, memberId, size = 36 }: AvatarProps) {
  const initials = `${(firstName || '?')[0]}${(lastName || '?')[0]}`.toUpperCase();

  return (
    <div
      className="avatar"
      style={{
        width: size,
        height: size,
        minWidth: size,
        borderRadius: '50%',
        background: hslColor(memberId),
        color: 'white',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: size * 0.38,
        fontWeight: 600,
        letterSpacing: '0.5px',
      }}
    >
      {initials}
    </div>
  );
}

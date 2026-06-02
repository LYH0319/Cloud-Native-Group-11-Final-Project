export type Role = 'developer' | 'operator' | 'admin';

export interface User {
  id: string;
  role: Role;
  token?: string;
}

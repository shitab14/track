export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T | null;
}

export type Role = 'admin' | 'team_member' | 'observer';

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
}

export interface Team {
  id: string;
  name: string;
}

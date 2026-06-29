import { request } from "./http";
import type { User } from "@/types";

// 用户列表（管理员）
export function listUsers(): Promise<User[]> {
  return request<User[]>({ url: "/users", method: "GET" });
}

export interface CreateUserPayload {
  username: string;
  password: string;
  role: string;
  display_name?: string;
}

// 新建用户（管理员）
export function createUser(payload: CreateUserPayload): Promise<User> {
  return request<User>({ url: "/users", method: "POST", data: payload });
}

export interface UpdateUserPayload {
  password?: string;
  role?: string;
  display_name?: string;
  is_active?: boolean;
}

// 更新用户（改角色/重置密码/启停）
export function updateUser(
  id: string,
  payload: UpdateUserPayload
): Promise<User> {
  return request<User>({ url: `/users/${id}`, method: "PUT", data: payload });
}

// 删除用户
export function deleteUser(id: string): Promise<unknown> {
  return request({ url: `/users/${id}`, method: "DELETE" });
}

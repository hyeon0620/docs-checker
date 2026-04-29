/**
 * API クライアント。バックエンド（:8000）を Cookie 認証で叩く薄いラッパ。
 *
 * - 全リクエストで `credentials: 'include'`（HttpOnly Cookie 送信のため）
 * - JSON ヘッダ自動付与
 * - エンドポイントごとの関数を export し、呼び出し側は型付きで使う
 */

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

// === 型 ===

export type User = {
	id: number;
	username: string;
	role: "user" | "admin";
};

export type IssueItem = {
	category: string; // "typo" | "keigo" | "expression"
	span: string;
	suggestion: string;
	reason: string;
};

export type CorrectResult = {
	corrected: string;
	score: number;
	issues: IssueItem[];
};

// === 共通 fetch ラッパ ===

async function api(path: string, init: RequestInit = {}): Promise<Response> {
	return fetch(`${BASE}${path}`, {
		...init,
		credentials: "include",
		headers: {
			"Content-Type": "application/json",
			...(init.headers ?? {}),
		},
	});
}

// === 認証 ===

export async function login(username: string, password: string): Promise<User> {
	const res = await api("/api/login", {
		method: "POST",
		body: JSON.stringify({ username, password }),
	});
	if (!res.ok) throw new Error("login failed");
	return res.json();
}

export async function logout(): Promise<void> {
	await api("/api/logout", { method: "POST" });
}

export async function me(): Promise<User> {
	const res = await api("/api/me");
	if (!res.ok) throw new Error("not authenticated");
	return res.json();
}

// === 校正 ===

export async function correct(original: string): Promise<CorrectResult> {
	const res = await api("/api/correct", {
		method: "POST",
		body: JSON.stringify({ original }),
	});
	if (!res.ok) throw new Error("correction failed");
	return res.json();
}

// === 管理者 ===

export type AdminUser = {
	id: number;
	username: string;
	role: "user" | "admin";
	is_active: boolean;
};

export async function listUsers(): Promise<AdminUser[]> {
	const res = await api("/api/admin/users");
	if (!res.ok) throw new Error("not allowed");
	return res.json();
}

export async function createUser(username: string, password: string): Promise<AdminUser> {
	const res = await api("/api/admin/user", {
		method: "POST",
		body: JSON.stringify({ username, password }),
	});
	if (res.status === 409) throw new Error("そのユーザー名は既に使われています");
	if (!res.ok) throw new Error("ユーザー作成に失敗しました");
	return res.json();
}

export async function deactivateUser(id: number): Promise<AdminUser> {
	const res = await api(`/api/admin/user/${id}/deactivate`, { method: "PATCH" });
	if (!res.ok) throw new Error("無効化に失敗しました");
	return res.json();
}

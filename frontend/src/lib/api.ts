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

/**
 * 認証状態を保持するストア（Svelte 5 runes ベース）。
 *
 * - HttpOnly Cookie に JWT が乗っているので、フロントは token を持たない
 * - 起動時に /api/me を叩いて user を取得（成功 = ログイン済）
 * - login/logout でこの状態を更新する
 */

import { goto } from "$app/navigation";
import * as api from "$lib/api";

class AuthStore {
	user = $state<api.User | null>(null);
	isLoading = $state(true);

	get isAuthenticated(): boolean {
		return this.user !== null;
	}

	/** アプリ起動時（+layout の onMount 内）：Cookie が有効なら user を復元する。 */
	async init(): Promise<void> {
		try {
			this.user = await api.me();
		} catch {
			this.user = null;
		} finally {
			this.isLoading = false;
		}
	}

	/** ログイン時：API を叩いて user を保存。Cookie はサーバ側で Set-Cookie される。 */
	async login(username: string, password: string): Promise<void> {
		this.user = await api.login(username, password);
	}

	/** ログアウト時：Cookie をサーバ側で削除し、user をクリアして /login へ。 */
	async logout(): Promise<void> {
		await api.logout();
		this.user = null;
		await goto("/login");
	}
}

export const authStore = new AuthStore();

<script lang="ts">
	import "./layout.css";
	import favicon from "$lib/assets/favicon.svg";
	import { goto } from "$app/navigation";
	import { page } from "$app/state";
	import { onMount } from "svelte";
	import { authStore } from "$lib/stores/auth.svelte";
	import { Button } from "$lib/components/ui/button";

	let { children } = $props();

	onMount(async () => {
		await authStore.init();
	});

	// 認証ガード：未ログイン → /login、/login に居るログイン済み → /
	$effect(() => {
		if (authStore.isLoading) return;
		const path = page.url.pathname;
		if (!authStore.isAuthenticated && path !== "/login") {
			goto("/login");
		} else if (authStore.isAuthenticated && path === "/login") {
			goto("/");
		}
	});
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

{#if authStore.isLoading}
	<div class="text-muted-foreground flex h-screen items-center justify-center">読み込み中…</div>
{:else}
	{#if authStore.isAuthenticated}
		<header class="flex items-center justify-end gap-3 border-b px-6 py-3">
			<span class="text-muted-foreground text-sm">{authStore.user?.username}</span>
			<Button variant="ghost" size="sm" onclick={() => goto("/")}>校正</Button>
			{#if authStore.user?.role === "admin"}
				<Button variant="ghost" size="sm" onclick={() => goto("/admin")}>管理</Button>
			{/if}
			<Button variant="ghost" size="sm" onclick={() => authStore.logout()}>ログアウト</Button>
		</header>
	{/if}
	<main>{@render children()}</main>
{/if}

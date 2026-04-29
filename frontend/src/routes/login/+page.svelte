<script lang="ts">
	import { goto } from "$app/navigation";
	import { Button } from "$lib/components/ui/button";
	import * as Card from "$lib/components/ui/card";
	import { Input } from "$lib/components/ui/input";
	import { Label } from "$lib/components/ui/label";
	import { authStore } from "$lib/stores/auth.svelte";

	let username = $state("");
	let password = $state("");
	let error = $state<string | null>(null);
	let loading = $state(false);

	async function submit(e: SubmitEvent) {
		e.preventDefault();
		loading = true;
		error = null;
		try {
			await authStore.login(username, password);
			await goto("/");
		} catch {
			error = "ユーザー名かパスワードが違います";
		} finally {
			loading = false;
		}
	}
</script>

<div class="flex min-h-screen items-center justify-center px-4">
	<Card.Root class="w-full max-w-sm">
		<Card.Header>
			<Card.Title class="text-2xl">ログイン</Card.Title>
			<Card.Description>社内アカウントでサインインしてください</Card.Description>
		</Card.Header>
		<Card.Content>
			<form onsubmit={submit} class="flex flex-col gap-4">
				<div class="flex flex-col gap-1.5">
					<Label for="username">ユーザー名</Label>
					<Input id="username" bind:value={username} required autocomplete="username" />
				</div>
				<div class="flex flex-col gap-1.5">
					<Label for="password">パスワード</Label>
					<Input
						id="password"
						type="password"
						bind:value={password}
						required
						autocomplete="current-password"
					/>
				</div>
				{#if error}
					<p class="text-destructive text-sm">{error}</p>
				{/if}
				<Button type="submit" class="w-full" disabled={loading}>
					{loading ? "ログイン中…" : "ログイン"}
				</Button>
			</form>
		</Card.Content>
	</Card.Root>
</div>

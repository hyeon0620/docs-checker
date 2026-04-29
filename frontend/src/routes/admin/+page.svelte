<script lang="ts">
	import { goto } from "$app/navigation";
	import {
		createUser,
		deactivateUser,
		listUsers,
		type AdminUser,
	} from "$lib/api";
	import * as Alert from "$lib/components/ui/alert";
	import { Badge } from "$lib/components/ui/badge";
	import { Button } from "$lib/components/ui/button";
	import * as Card from "$lib/components/ui/card";
	import { Input } from "$lib/components/ui/input";
	import { Label } from "$lib/components/ui/label";
	import * as Table from "$lib/components/ui/table";
	import { authStore } from "$lib/stores/auth.svelte";
	import { onMount } from "svelte";

	let users = $state<AdminUser[]>([]);
	let listError = $state<string | null>(null);
	let formUsername = $state("");
	let formPassword = $state("");
	let formError = $state<string | null>(null);
	let creating = $state(false);

	// admin 専用：admin でなければ / に戻す
	$effect(() => {
		if (authStore.isLoading) return;
		if (authStore.user?.role !== "admin") goto("/");
	});

	async function refresh() {
		try {
			users = await listUsers();
			listError = null;
		} catch {
			listError = "ユーザー一覧の取得に失敗しました";
		}
	}

	onMount(refresh);

	async function submit(e: SubmitEvent) {
		e.preventDefault();
		creating = true;
		formError = null;
		try {
			await createUser(formUsername, formPassword);
			formUsername = "";
			formPassword = "";
			await refresh();
		} catch (err) {
			formError = err instanceof Error ? err.message : "作成に失敗しました";
		} finally {
			creating = false;
		}
	}

	async function onDeactivate(user: AdminUser) {
		if (!confirm(`${user.username} を無効化しますか？`)) return;
		try {
			await deactivateUser(user.id);
			await refresh();
		} catch {
			listError = "無効化に失敗しました";
		}
	}
</script>

<div class="mx-auto w-full max-w-4xl space-y-8 p-6">
	<header>
		<h1 class="text-2xl font-bold">管理画面</h1>
		<p class="text-muted-foreground text-sm">ユーザーの登録と無効化</p>
	</header>

	<Card.Root>
		<Card.Header><Card.Title>ユーザー登録</Card.Title></Card.Header>
		<Card.Content>
			<form onsubmit={submit} class="flex flex-col gap-3 sm:flex-row sm:items-end">
				<div class="flex-1 space-y-1.5">
					<Label for="new-username">ユーザー名</Label>
					<Input id="new-username" bind:value={formUsername} required />
				</div>
				<div class="flex-1 space-y-1.5">
					<Label for="new-password">初期パスワード</Label>
					<Input id="new-password" type="password" bind:value={formPassword} required />
				</div>
				<Button type="submit" disabled={creating}>
					{creating ? "登録中…" : "登録"}
				</Button>
			</form>
			{#if formError}
				<p class="text-destructive mt-2 text-sm">{formError}</p>
			{/if}
		</Card.Content>
	</Card.Root>

	<Card.Root>
		<Card.Header><Card.Title>ユーザー一覧</Card.Title></Card.Header>
		<Card.Content>
			{#if listError}
				<Alert.Root variant="destructive"><Alert.Description>{listError}</Alert.Description></Alert.Root>
			{/if}
			<Table.Root>
				<Table.Header>
					<Table.Row>
						<Table.Head class="w-12">ID</Table.Head>
						<Table.Head>ユーザー名</Table.Head>
						<Table.Head>ロール</Table.Head>
						<Table.Head>状態</Table.Head>
						<Table.Head class="text-right">操作</Table.Head>
					</Table.Row>
				</Table.Header>
				<Table.Body>
					{#each users as user (user.id)}
						<Table.Row>
							<Table.Cell>{user.id}</Table.Cell>
							<Table.Cell>{user.username}</Table.Cell>
							<Table.Cell>
								<Badge variant={user.role === "admin" ? "default" : "outline"}>
									{user.role}
								</Badge>
							</Table.Cell>
							<Table.Cell>
								{#if user.is_active}
									<Badge variant="outline">有効</Badge>
								{:else}
									<Badge variant="destructive">無効</Badge>
								{/if}
							</Table.Cell>
							<Table.Cell class="text-right">
								{#if user.is_active && user.id !== authStore.user?.id}
									<Button variant="ghost" size="sm" onclick={() => onDeactivate(user)}>
										無効化
									</Button>
								{/if}
							</Table.Cell>
						</Table.Row>
					{/each}
				</Table.Body>
			</Table.Root>
		</Card.Content>
	</Card.Root>
</div>

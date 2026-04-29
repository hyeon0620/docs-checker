<script lang="ts">
	import { correct, type CorrectResult } from "$lib/api";
	import * as Alert from "$lib/components/ui/alert";
	import { Badge } from "$lib/components/ui/badge";
	import { Button } from "$lib/components/ui/button";
	import * as Card from "$lib/components/ui/card";
	import { Skeleton } from "$lib/components/ui/skeleton";
	import { Textarea } from "$lib/components/ui/textarea";

	let original = $state("");
	let result = $state<CorrectResult | null>(null);
	let loading = $state(false);
	let error = $state<string | null>(null);

	async function submit() {
		if (!original.trim()) return;
		loading = true;
		error = null;
		result = null;
		try {
			result = await correct(original);
		} catch {
			error = "校正中にエラーが発生しました";
		} finally {
			loading = false;
		}
	}
</script>

<div class="mx-auto w-full max-w-3xl space-y-6 p-6">
	<header>
		<h1 class="text-2xl font-bold">メール校正</h1>
		<p class="text-muted-foreground text-sm">誤字・敬語・自然な表現をチェックします</p>
	</header>

	<div class="space-y-3">
		<Textarea bind:value={original} rows={10} placeholder="校正したい文章を入力…" />
		<Button onclick={submit} disabled={loading || !original.trim()}>
			{loading ? "校正中…" : "校正する"}
		</Button>
	</div>

	{#if loading}
		<Skeleton class="h-32" />
	{/if}

	{#if error}
		<Alert.Root variant="destructive">
			<Alert.Description>{error}</Alert.Description>
		</Alert.Root>
	{/if}

	{#if result}
		<Card.Root>
			<Card.Header class="flex flex-row items-center justify-between">
				<Card.Title>結果</Card.Title>
				<Badge>{result.score}点</Badge>
			</Card.Header>
			<Card.Content class="space-y-4">
				<section>
					<h3 class="mb-1 font-semibold">修正後</h3>
					<p class="bg-muted/40 rounded p-3 text-sm whitespace-pre-wrap">{result.corrected}</p>
				</section>

				{#if result.issues.length > 0}
					<section>
						<h3 class="mb-2 font-semibold">指摘事項（{result.issues.length}件）</h3>
						<ul class="space-y-3">
							{#each result.issues as issue}
								<li class="border-border space-y-1 border-l-2 pl-3">
									<Badge variant="outline">{issue.category}</Badge>
									<p class="text-sm">
										「<span class="font-mono">{issue.span}</span>」 → 「<span class="font-mono"
											>{issue.suggestion}</span
										>」
									</p>
									<p class="text-muted-foreground text-xs">{issue.reason}</p>
								</li>
							{/each}
						</ul>
					</section>
				{:else}
					<p class="text-muted-foreground text-sm">指摘事項なし。完璧です！</p>
				{/if}
			</Card.Content>
		</Card.Root>
	{/if}
</div>

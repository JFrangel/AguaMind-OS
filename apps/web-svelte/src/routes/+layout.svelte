<script lang="ts">
  import "../app.css";
  import { onMount } from "svelte";
  import { QueryClient, QueryClientProvider } from "@tanstack/svelte-query";

  import ImageLightbox from "$lib/components/ImageLightbox.svelte";
  import { theme } from "$lib/stores/theme.svelte";

  let { children } = $props();

  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { staleTime: 30_000, refetchOnWindowFocus: false },
    },
  });

  onMount(() => theme.init());
</script>

<QueryClientProvider client={queryClient}>
  {@render children?.()}
  <ImageLightbox />
</QueryClientProvider>

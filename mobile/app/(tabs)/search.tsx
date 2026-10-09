import { useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Pressable, RefreshControl, ScrollView, Text, View } from "react-native";
import { SearchInput } from "@/components/SearchInput";
import { Snippet } from "@/components/Snippet";
import { Card, EmptyState, ErrorNote, FileTag, Loading, Pill, Screen, SectionCard } from "@/components/ui";
import { useWorkspace } from "@/context/WorkspaceContext";
import { useDocuments } from "@/hooks/useDocuments";
import { fileExtension, formatRelative } from "@/lib/format";
import { searchService } from "@/services/search";
import { colors, space } from "@/theme";
import type { SearchHistoryItem, SearchResponse } from "@/types/api";

const TYPE_LABEL: Record<string, string> = { pdf: "PDF", md: "Markdown", txt: "Text", docx: "Word" };

export default function SearchScreen() {
  const router = useRouter();
  const { q = "" } = useLocalSearchParams<{ q?: string }>();
  const { current } = useWorkspace();
  const workspaceId = current?.id ?? null;
  const { documents } = useDocuments(workspaceId);
  const docById = useMemo(() => new Map(documents.map((d) => [d.id, d])), [documents]);

  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);
  const ctrl = useRef<AbortController | null>(null);

  const run = useCallback(
    async (query: string) => {
      if (!workspaceId || !query) return;
      ctrl.current?.abort();
      const c = new AbortController();
      ctrl.current = c;
      setLoading(true);
      setError(null);
      setTypeFilter(null);
      try {
        setResponse(await searchService.search(workspaceId, query, 20, c.signal));
        searchService.history(workspaceId, 8).then(setHistory).catch(() => {});
      } catch (e) {
        if ((e as Error).name !== "AbortError") setError((e as Error).message);
      } finally {
        if (ctrl.current === c) setLoading(false);
      }
    },
    [workspaceId],
  );

  // The route param is the source of truth for the query (deep links, history taps, home search).
  useEffect(() => {
    if (q) void run(q);
    else setResponse(null);
  }, [q, run]);

  useEffect(() => {
    if (workspaceId) searchService.history(workspaceId, 8).then(setHistory).catch(() => setHistory([]));
  }, [workspaceId]);

  const submit = (query: string) => router.setParams({ q: query });

  const types = response ? Array.from(new Set(response.results.map((r) => fileExtension(r.filename)).filter(Boolean))) : [];
  const shown = response ? response.results.filter((r) => !typeFilter || fileExtension(r.filename) === typeFilter) : [];

  return (
    <Screen>
      <ScrollView
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={{ padding: 16, gap: 14, paddingBottom: 40 }}
        refreshControl={<RefreshControl refreshing={loading && !!response} onRefresh={() => run(q)} tintColor={colors.ember} />}
      >
        <SearchInput workspaceId={workspaceId} initialValue={q} onSubmit={submit} />

        {!current && <EmptyState title="Create a workspace first" body="Search works inside a workspace. Open the Profile tab → Workspaces." />}

        {response && types.length > 0 && (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8 }} keyboardShouldPersistTaps="handled">
            {[null, ...types].map((t) => (
              <Pill key={t ?? "all"} label={t ? (TYPE_LABEL[t] ?? `.${t}`) : "All"} active={typeFilter === t} onPress={() => setTypeFilter(t)} />
            ))}
          </ScrollView>
        )}

        {error && <ErrorNote message={error} onRetry={() => run(q)} />}
        {loading && !response && <Loading label="Searching…" />}

        {!q && !loading && current && (
          history.length > 0 ? (
            <Card style={{ padding: space.lg }}>
              <Text style={{ color: colors.fg, fontSize: 17, fontWeight: "600", marginBottom: 4 }}>Recent searches</Text>
              {history.map((h, i) => (
                <Pressable key={h.id} onPress={() => submit(h.query_text)} style={{ paddingVertical: 12, borderTopWidth: i ? 1 : 0, borderTopColor: colors.lineSoft }}>
                  <Text style={{ color: colors.fg, fontSize: 15 }}>{h.query_text}</Text>
                </Pressable>
              ))}
            </Card>
          ) : (
            <EmptyState title="Search everything you’ve saved" body="Type a word or phrase you remember. Put quotes around words to find an exact phrase." />
          )
        )}

        {response && !error && (
          <SectionCard title="Your Knowledge" icon="document-text-outline" count={shown.length}>
            {shown.length === 0 ? (
              <EmptyState title="No matches" body={`Nothing in ${current?.name} matches “${response.query}”. Try fewer or different words. Only documents marked Ready can be searched.`} />
            ) : (
              shown.map((r, i) => {
                const doc = docById.get(r.document_id);
                return (
                  <Pressable
                    key={r.document_id}
                    accessibilityRole="button"
                    accessibilityLabel={`Open ${r.filename}`}
                    onPress={() => router.push({ pathname: "/document/[id]", params: { id: r.document_id, q: response.query } })}
                    style={({ pressed }) => ({ flexDirection: "row", gap: 12, paddingVertical: 14, borderTopWidth: i ? 1 : 0, borderTopColor: "rgba(255,255,255,0.08)", opacity: pressed ? 0.7 : 1 })}
                  >
                    <FileTag filename={r.filename} />
                    <View style={{ flex: 1 }}>
                      <Text style={{ color: colors.fg, fontWeight: "700", fontSize: 15.5 }} numberOfLines={1}>{r.filename}</Text>
                      <Snippet snippet={r.snippet} style={{ color: colors.muted, fontSize: 14.5, lineHeight: 21, marginTop: 3 }} />
                      {doc && <Text style={{ color: colors.faint, fontSize: 12, marginTop: 6 }}>Added {formatRelative(doc.created_at)}</Text>}
                    </View>
                  </Pressable>
                );
              })
            )}
          </SectionCard>
        )}
      </ScrollView>
    </Screen>
  );
}

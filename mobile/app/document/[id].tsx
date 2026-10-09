import { Ionicons } from "@expo/vector-icons";
import { Stack, useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Alert, KeyboardAvoidingView, Platform, Pressable, ScrollView, Text, TextInput, View } from "react-native";
import { Button, ErrorNote, FileTag, Loading, Screen, StatusBadge } from "@/components/ui";
import { useWorkspace } from "@/context/WorkspaceContext";
import { formatBytes, formatDateTime } from "@/lib/format";
import { escapeRegExp, queryTerms } from "@/lib/highlight";
import { documentService } from "@/services/documents";
import { colors, radius } from "@/theme";
import type { EmberDocument } from "@/types/api";

const MAX_CHARS = 200_000; // keeps the screen responsive on very large documents

interface Block {
  parts: { s: string; hit: number | null }[];
  firstHit: number;
  hitCount: number;
}

export default function DocumentScreen() {
  const { id, q = "" } = useLocalSearchParams<{ id: string; q?: string }>();
  const router = useRouter();
  const { current } = useWorkspace();
  const workspaceId = current?.id ?? null;

  const [doc, setDoc] = useState<EmberDocument | null>(null);
  const [text, setText] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [textError, setTextError] = useState<string | null>(null);
  const [terms, setTerms] = useState(() => queryTerms(q));
  const [termInput, setTermInput] = useState(q);
  const [active, setActive] = useState(0);
  const [zoom, setZoom] = useState(100);

  const scroller = useRef<ScrollView>(null);
  const ys = useRef<number[]>([]);

  const load = useCallback(async () => {
    if (!workspaceId || !id) return;
    try {
      const d = await documentService.get(workspaceId, id);
      setDoc(d);
      setError(null);
      if (d.status === "READY") documentService.text(workspaceId, id).then((t) => setText(t.text)).catch((e) => setTextError((e as Error).message));
    } catch (e) {
      setError((e as Error).message);
    }
  }, [workspaceId, id]);

  useEffect(() => {
    void load();
  }, [load]);

  // Poll while the document is still being processed.
  useEffect(() => {
    if (!doc || !["UPLOADING", "PROCESSING", "INDEXING"].includes(doc.status)) return;
    const t = setTimeout(load, 2000);
    return () => clearTimeout(t);
  }, [doc, load]);

  const { blocks, hitCount, truncated } = useMemo(() => {
    if (text === null) return { blocks: [] as Block[], hitCount: 0, truncated: false };
    const body = text.length > MAX_CHARS ? text.slice(0, MAX_CHARS) : text;
    const re = terms.length ? new RegExp(`(${terms.map(escapeRegExp).join("|")})`, "gi") : null;
    let n = 0;
    const out: Block[] = body.split(/\n{2,}/).filter((p) => p.trim()).map((para) => {
      const first = n;
      const parts = re ? para.split(re).map((s, i) => (i % 2 === 1 ? { s, hit: n++ } : { s, hit: null })) : [{ s: para, hit: null }];
      return { parts, firstHit: first, hitCount: n - first };
    });
    return { blocks: out, hitCount: n, truncated: text.length > MAX_CHARS };
  }, [text, terms]);

  // Scroll to the active match: find its paragraph, then its measured offset.
  useEffect(() => {
    if (!hitCount) return;
    const bi = blocks.findIndex((b) => active >= b.firstHit && active < b.firstHit + b.hitCount);
    const y = ys.current[bi];
    if (bi >= 0 && y !== undefined) scroller.current?.scrollTo({ y: Math.max(0, y - 24), animated: true });
  }, [active, hitCount, blocks]);

  const step = (d: number) => hitCount && setActive((a) => (a + d + hitCount) % hitCount);
  const find = () => {
    setTerms(queryTerms(termInput));
    setActive(0);
  };

  const confirmDelete = () => {
    if (!workspaceId || !doc) return;
    const go = async () => {
      try {
        await documentService.remove(workspaceId, doc.id);
        router.back();
      } catch (e) {
        setError((e as Error).message);
      }
    };
    if (Platform.OS === "web") {
      if (window.confirm(`Delete “${doc.filename}”?`)) void go();
    } else Alert.alert(`Delete “${doc.filename}”?`, "This can’t be undone.", [{ text: "Cancel", style: "cancel" }, { text: "Delete", style: "destructive", onPress: () => void go() }]);
  };

  const processing = doc && ["UPLOADING", "PROCESSING", "INDEXING"].includes(doc.status);
  const fontSize = (15 * zoom) / 100;

  return (
    <Screen topInset={false}>
      <Stack.Screen options={{ title: "Document", headerRight: () => (doc ? <Pressable onPress={confirmDelete} hitSlop={10} accessibilityLabel="Delete document"><Ionicons name="trash-outline" size={20} color={colors.muted} /></Pressable> : null) }} />
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined} keyboardVerticalOffset={90}>
        {error ? (
          <View style={{ padding: 16 }}><ErrorNote message={error} onRetry={load} /></View>
        ) : !doc ? (
          <View style={{ padding: 16 }}><Loading /></View>
        ) : (
          <>
            <View style={{ padding: 14, gap: 10, borderBottomWidth: 1, borderBottomColor: colors.lineSoft, backgroundColor: colors.bg }}>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 12 }}>
                <FileTag filename={doc.filename} size={40} />
                <View style={{ flex: 1, gap: 3 }}>
                  <Text style={{ color: colors.fg, fontSize: 15, fontWeight: "700" }} numberOfLines={1}>{doc.filename}</Text>
                  <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
                    <StatusBadge status={doc.status} />
                    <Text style={{ color: colors.faint, fontSize: 12 }}>{formatBytes(doc.file_size_bytes)} · {formatDateTime(doc.created_at)}</Text>
                  </View>
                </View>
              </View>

              {doc.status === "READY" && (
                <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
                  <View style={{ flex: 1, flexDirection: "row", alignItems: "center", gap: 8, backgroundColor: colors.sunken, borderRadius: radius.md, borderWidth: 1, borderColor: colors.line, paddingHorizontal: 10, height: 42 }}>
                    <Ionicons name="search" size={16} color={colors.muted} />
                    <TextInput
                      value={termInput}
                      onChangeText={setTermInput}
                      onSubmitEditing={find}
                      placeholder="Find in this document"
                      placeholderTextColor={colors.faint}
                      returnKeyType="search"
                      autoCapitalize="none"
                      autoCorrect={false}
                      accessibilityLabel="Find in this document"
                      style={[{ flex: 1, color: colors.fg, fontSize: 15, paddingVertical: 0 }, { outlineStyle: "none" } as object]}
                    />
                  </View>
                  <Text style={{ color: colors.muted, fontSize: 12.5, minWidth: 48, textAlign: "center" }} accessibilityLiveRegion="polite">
                    {terms.length ? (hitCount ? `${active + 1}/${hitCount}` : "None") : ""}
                  </Text>
                  <Pressable accessibilityLabel="Previous match" disabled={!hitCount} onPress={() => step(-1)} hitSlop={8} style={{ opacity: hitCount ? 1 : 0.35 }}><Ionicons name="chevron-up" size={22} color={colors.fg} /></Pressable>
                  <Pressable accessibilityLabel="Next match" disabled={!hitCount} onPress={() => step(1)} hitSlop={8} style={{ opacity: hitCount ? 1 : 0.35 }}><Ionicons name="chevron-down" size={22} color={colors.fg} /></Pressable>
                </View>
              )}
            </View>

            {doc.status === "FAILED" && <View style={{ padding: 16 }}><ErrorNote message="Ember couldn’t read the text in this file. Re-index it from the Knowledge tab, or upload a different copy." /></View>}
            {processing && <View style={{ padding: 16 }}><Loading label="Ember is reading this document…" /></View>}

            {doc.status === "READY" && (
              <>
                <ScrollView ref={scroller} style={{ flex: 1 }} contentContainerStyle={{ padding: 12, paddingBottom: 90 }} keyboardShouldPersistTaps="handled">
                  <View style={{ backgroundColor: colors.paper, borderRadius: 8, padding: 18, minHeight: 300 }}>
                    {textError ? (
                      <Text style={{ color: "#b3321f" }}>{textError}</Text>
                    ) : text === null ? (
                      <Loading label="Loading text…" />
                    ) : (
                      blocks.map((b, bi) => (
                        <Text
                          key={bi}
                          onLayout={(e) => {
                            ys.current[bi] = e.nativeEvent.layout.y + 30; // + paper padding offset
                          }}
                          style={{ color: colors.paperInk, fontSize, lineHeight: fontSize * 1.65, marginBottom: fontSize * 0.9 }}
                        >
                          {b.parts.map((p, pi) =>
                            p.hit === null ? (
                              <Text key={pi}>{p.s}</Text>
                            ) : (
                              <Text key={pi} style={p.hit === active ? { backgroundColor: "#f0661f", color: "#fff", fontWeight: "700" } : { backgroundColor: "#ffd9b8", color: colors.paperInk }}>
                                {p.s}
                              </Text>
                            ),
                          )}
                        </Text>
                      ))
                    )}
                    {truncated && <Text style={{ color: "#64748b", fontSize: 12, marginTop: 8 }}>Showing the first {MAX_CHARS.toLocaleString()} characters.</Text>}
                  </View>
                </ScrollView>

                <View style={{ position: "absolute", right: 14, bottom: 18, flexDirection: "row", alignItems: "center", backgroundColor: colors.surface, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.line, paddingHorizontal: 6 }}>
                  <Pressable accessibilityLabel="Smaller text" disabled={zoom <= 70} onPress={() => setZoom((z) => Math.max(70, z - 10))} style={{ padding: 10, opacity: zoom <= 70 ? 0.35 : 1 }}><Ionicons name="remove" size={18} color={colors.fg} /></Pressable>
                  <Text style={{ color: colors.fg, fontSize: 13, minWidth: 40, textAlign: "center" }}>{zoom}%</Text>
                  <Pressable accessibilityLabel="Larger text" disabled={zoom >= 160} onPress={() => setZoom((z) => Math.min(160, z + 10))} style={{ padding: 10, opacity: zoom >= 160 ? 0.35 : 1 }}><Ionicons name="add" size={18} color={colors.fg} /></Pressable>
                </View>
              </>
            )}
          </>
        )}
      </KeyboardAvoidingView>
    </Screen>
  );
}

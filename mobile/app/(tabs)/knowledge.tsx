import { Ionicons } from "@expo/vector-icons";
import * as DocumentPicker from "expo-document-picker";
import { useRouter } from "expo-router";
import { useRef, useState } from "react";
import { ActionSheetIOS, Alert, FlatList, Platform, Pressable, RefreshControl, Text, View } from "react-native";
import { Button, Card, EmptyState, ErrorNote, FileTag, Loading, Screen, ScreenTitle, StatusBadge } from "@/components/ui";
import { useWorkspace } from "@/context/WorkspaceContext";
import { useDocuments } from "@/hooks/useDocuments";
import { fileExtension, formatBytes, formatRelative } from "@/lib/format";
import { documentService } from "@/services/documents";
import { colors, space } from "@/theme";
import type { EmberDocument } from "@/types/api";

const ALLOWED = ["pdf", "txt", "md", "docx"];
const MAX_BYTES = 25 * 1024 * 1024;
const MIME: Record<string, string> = {
  pdf: "application/pdf",
  txt: "text/plain",
  md: "text/markdown",
  docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
};

interface UploadItem {
  id: number;
  name: string;
  progress: number;
  state: "uploading" | "done" | "duplicate" | "error";
  message?: string;
}

function confirm(title: string, message: string, onYes: () => void) {
  if (Platform.OS === "web") {
    if (window.confirm(`${title}\n${message}`)) onYes();
    return;
  }
  Alert.alert(title, message, [{ text: "Cancel", style: "cancel" }, { text: "Delete", style: "destructive", onPress: onYes }]);
}

export default function KnowledgeScreen() {
  const router = useRouter();
  const { current } = useWorkspace();
  const { documents, loading, error, reload } = useDocuments(current?.id ?? null);
  const [items, setItems] = useState<UploadItem[]>([]);
  const [actionError, setActionError] = useState<string | null>(null);
  const counter = useRef(0);

  const patch = (id: number, p: Partial<UploadItem>) => setItems((prev) => prev.map((i) => (i.id === id ? { ...i, ...p } : i)));

  /**
   * File picking uses the system document picker (iOS Files / Android Storage Access Framework),
   * so Ember never needs broad storage permissions: the user grants access to just the files they choose.
   */
  const pick = async () => {
    if (!current) return;
    const res = await DocumentPicker.getDocumentAsync({ type: "*/*", multiple: true, copyToCacheDirectory: true });
    if (res.canceled) return;
    for (const asset of res.assets) {
      const id = ++counter.current;
      const ext = fileExtension(asset.name);
      let problem: string | null = null;
      if (!ALLOWED.includes(ext)) problem = "Unsupported file type. Use PDF, TXT, Markdown or DOCX.";
      else if (asset.size && asset.size > MAX_BYTES) problem = `This file is ${formatBytes(asset.size)}. The maximum is 25 MB.`;
      else if (asset.size === 0) problem = "This file is empty.";
      setItems((prev) => [{ id, name: asset.name, progress: 0, state: problem ? "error" : "uploading", message: problem ?? undefined }, ...prev]);
      if (problem) continue;
      try {
        const r = await documentService.upload(current.id, { uri: asset.uri, name: asset.name, mimeType: MIME[ext], file: asset.file }, null, (f) => patch(id, { progress: f }));
        patch(id, r.is_duplicate ? { state: "duplicate", progress: 1, message: "Already in this workspace." } : { state: "done", progress: 1 });
        void reload();
      } catch (e) {
        patch(id, { state: "error", message: (e as Error).message });
      }
    }
  };

  const act = async (fn: () => Promise<unknown>) => {
    setActionError(null);
    try {
      await fn();
      await reload();
    } catch (e) {
      setActionError((e as Error).message);
    }
  };

  const openMenu = (d: EmberDocument) => {
    if (!current) return;
    const doReindex = () => void act(() => documentService.reindex(current.id, d.id));
    const doDelete = () => confirm(`Delete “${d.filename}”?`, "This can’t be undone.", () => void act(() => documentService.remove(current.id, d.id)));
    if (Platform.OS === "ios") {
      ActionSheetIOS.showActionSheetWithOptions({ options: ["Cancel", "Re-index", "Delete"], cancelButtonIndex: 0, destructiveButtonIndex: 2, title: d.filename }, (i) => (i === 1 ? doReindex() : i === 2 ? doDelete() : undefined));
    } else if (Platform.OS === "web") {
      if (window.confirm(`Re-index “${d.filename}”? (Cancel to delete instead)`)) doReindex();
      else doDelete();
    } else {
      Alert.alert(d.filename, undefined, [{ text: "Re-index", onPress: doReindex }, { text: "Delete", style: "destructive", onPress: doDelete }, { text: "Cancel", style: "cancel" }]);
    }
  };

  const sorted = [...documents].sort((a, b) => b.created_at.localeCompare(a.created_at));

  return (
    <Screen>
      <FlatList
        data={current ? sorted : []}
        keyExtractor={(d) => d.id}
        contentContainerStyle={{ padding: 16, paddingBottom: 40 }}
        refreshControl={<RefreshControl refreshing={false} onRefresh={reload} tintColor={colors.ember} />}
        ListHeaderComponent={
          <View style={{ gap: 14, marginBottom: 12 }}>
            <ScreenTitle title="Knowledge" subtitle={current ? `Everything you’ve added to ${current.name}` : undefined} />
            {current && <Button title="Add documents" icon="cloud-upload-outline" onPress={pick} />}
            {items.slice(0, 5).map((i) => (
              <Card key={i.id} style={{ padding: 12 }}>
                <View style={{ flexDirection: "row", justifyContent: "space-between", gap: 10 }}>
                  <Text style={{ color: colors.fg, fontWeight: "600", flex: 1 }} numberOfLines={1}>{i.name}</Text>
                  <Text style={{ color: i.state === "error" ? colors.danger : i.state === "done" ? colors.ok : colors.muted, fontSize: 13 }}>
                    {i.state === "uploading" ? `${Math.round(i.progress * 100)}%` : i.state === "done" ? "Uploaded" : i.state === "duplicate" ? "Duplicate" : "Failed"}
                  </Text>
                </View>
                {i.state === "uploading" && (
                  <View style={{ height: 4, borderRadius: 2, backgroundColor: colors.sunken, marginTop: 8, overflow: "hidden" }}>
                    <View style={{ height: 4, width: `${i.progress * 100}%`, backgroundColor: colors.ember }} />
                  </View>
                )}
                {i.message && <Text style={{ color: i.state === "error" ? colors.danger : colors.muted, fontSize: 13, marginTop: 6 }}>{i.message}</Text>}
              </Card>
            ))}
            {(error || actionError) && <ErrorNote message={(error ?? actionError)!} onRetry={error ? reload : undefined} />}
          </View>
        }
        ListEmptyComponent={
          !current ? (
            <EmptyState title="Create a workspace first" body="Your knowledge lives inside a workspace." action={<Button title="Go to Workspaces" onPress={() => router.push("/workspaces")} />} />
          ) : loading ? (
            <Loading />
          ) : (
            <EmptyState title="No documents yet" body="Tap “Add documents” to pick PDFs, notes or Word files. Ember reads them and makes them searchable." />
          )
        }
        renderItem={({ item: d, index }) => (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={`Open ${d.filename}`}
            onPress={() => router.push({ pathname: "/document/[id]", params: { id: d.id } })}
            style={({ pressed }) => ({ flexDirection: "row", alignItems: "center", gap: 12, padding: 14, backgroundColor: pressed ? colors.sunken : colors.surface, borderTopLeftRadius: index === 0 ? 16 : 0, borderTopRightRadius: index === 0 ? 16 : 0, borderBottomLeftRadius: index === sorted.length - 1 ? 16 : 0, borderBottomRightRadius: index === sorted.length - 1 ? 16 : 0, borderTopWidth: index ? 1 : 0, borderTopColor: colors.lineSoft })}
          >
            <FileTag filename={d.filename} />
            <View style={{ flex: 1, gap: 3 }}>
              <Text style={{ color: colors.fg, fontWeight: "600", fontSize: 15 }} numberOfLines={1}>{d.filename}</Text>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
                <StatusBadge status={d.status} />
                <Text style={{ color: colors.faint, fontSize: 12 }}>{formatBytes(d.file_size_bytes)} · {formatRelative(d.created_at)}</Text>
              </View>
            </View>
            <Pressable accessibilityLabel={`Actions for ${d.filename}`} hitSlop={12} onPress={() => openMenu(d)}>
              <Ionicons name="ellipsis-horizontal" size={20} color={colors.muted} />
            </Pressable>
          </Pressable>
        )}
      />
    </Screen>
  );
}

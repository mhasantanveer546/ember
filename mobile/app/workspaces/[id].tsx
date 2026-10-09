import { Stack, useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useEffect, useMemo, useState } from "react";
import { FlatList, Pressable, ScrollView, Text, View } from "react-native";
import { Button, Card, EmptyState, ErrorNote, FileTag, Loading, Pill, Screen, StatusBadge } from "@/components/ui";
import { useWorkspace } from "@/context/WorkspaceContext";
import { useDocuments } from "@/hooks/useDocuments";
import { formatBytes, formatDateTime } from "@/lib/format";
import { workspaceService } from "@/services/workspaces";
import { colors } from "@/theme";
import type { Folder, IndexMetadata } from "@/types/api";

const ALL = "__all__";
const UNFILED = "__unfiled__";

export default function WorkspaceDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { workspaces, loading: wsLoading } = useWorkspace();
  const workspace = workspaces.find((w) => w.id === id) ?? null;
  const { documents, loading, error, reload } = useDocuments(workspace ? id : null);
  const [folders, setFolders] = useState<Folder[]>([]);
  const [meta, setMeta] = useState<IndexMetadata | null>(null);
  const [selected, setSelected] = useState<string>(ALL);
  const [rebuilding, setRebuilding] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const loadSide = useCallback(async () => {
    try {
      setFolders(await workspaceService.folders(id));
      setMeta(await workspaceService.indexMetadata(id).catch(() => null));
    } catch (e) {
      setActionError((e as Error).message);
    }
  }, [id]);

  useEffect(() => {
    if (workspace) void loadSide();
  }, [workspace, loadSide]);

  const visible = useMemo(() => documents.filter((d) => (selected === ALL ? true : selected === UNFILED ? d.folder_id === null : d.folder_id === selected)), [documents, selected]);

  if (wsLoading) return <Screen topInset={false}><View style={{ padding: 16 }}><Loading /></View></Screen>;
  if (!workspace) return <Screen topInset={false}><View style={{ padding: 16 }}><EmptyState title="Workspace not found" action={<Button title="Back" onPress={() => router.back()} />} /></View></Screen>;

  return (
    <Screen topInset={false}>
      <Stack.Screen options={{ title: workspace.name }} />
      <FlatList
        data={visible}
        keyExtractor={(d) => d.id}
        contentContainerStyle={{ padding: 16, gap: 10, paddingBottom: 40 }}
        ListHeaderComponent={
          <View style={{ gap: 14, marginBottom: 6 }}>
            <Card style={{ padding: 16, gap: 6 }}>
              <Text style={{ color: colors.fg, fontSize: 20, fontWeight: "700" }}>{workspace.name}</Text>
              {meta && <Text style={{ color: colors.muted, fontSize: 13.5, lineHeight: 20 }}>{meta.document_count} indexed {meta.document_count === 1 ? "document" : "documents"}, {meta.vocabulary_size.toLocaleString()} distinct words. Index v{meta.version}{meta.last_built_at ? `, rebuilt ${formatDateTime(meta.last_built_at)}` : ""}.</Text>}
              <View style={{ flexDirection: "row", gap: 8, marginTop: 8 }}>
                <Button title="Search" small icon="search" onPress={() => router.navigate("/search")} />
                <Button
                  title={rebuilding ? "Rebuilding…" : "Rebuild index"}
                  small
                  variant="secondary"
                  disabled={rebuilding}
                  onPress={async () => {
                    setRebuilding(true);
                    try {
                      await workspaceService.rebuildIndex(id);
                      await Promise.all([loadSide(), reload()]);
                    } catch (e) {
                      setActionError((e as Error).message);
                    }
                    setRebuilding(false);
                  }}
                />
              </View>
            </Card>
            {(actionError || error) && <ErrorNote message={(actionError ?? error)!} />}
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8 }}>
              <Pill label="All" active={selected === ALL} onPress={() => setSelected(ALL)} />
              <Pill label="Unfiled" active={selected === UNFILED} onPress={() => setSelected(UNFILED)} />
              {folders.map((f) => <Pill key={f.id} label={f.name} icon="folder-outline" active={selected === f.id} onPress={() => setSelected(f.id)} />)}
            </ScrollView>
          </View>
        }
        ListEmptyComponent={loading ? <Loading /> : <EmptyState title="No documents here" body="Add documents from the Knowledge tab, or pick another folder." />}
        renderItem={({ item: d }) => (
          <Pressable onPress={() => router.push({ pathname: "/document/[id]", params: { id: d.id } })} style={({ pressed }) => ({ flexDirection: "row", alignItems: "center", gap: 12, padding: 14, borderRadius: 14, backgroundColor: pressed ? colors.sunken : colors.surface, borderWidth: 1, borderColor: colors.lineSoft })}>
            <FileTag filename={d.filename} />
            <View style={{ flex: 1, gap: 3 }}>
              <Text style={{ color: colors.fg, fontWeight: "600", fontSize: 15 }} numberOfLines={1}>{d.filename}</Text>
              <Text style={{ color: colors.faint, fontSize: 12 }}>{formatBytes(d.file_size_bytes)}</Text>
            </View>
            <StatusBadge status={d.status} />
          </Pressable>
        )}
      />
    </Screen>
  );
}

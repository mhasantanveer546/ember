import { Ionicons } from "@expo/vector-icons";
import { type ReactNode } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View, type StyleProp, type TextStyle, type ViewStyle } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { fileExtension } from "@/lib/format";
import { colors, radius, space } from "@/theme";
import type { DocumentStatus } from "@/types/api";
import { EmberMark } from "./Logo";

export type IconName = keyof typeof Ionicons.glyphMap;

/** Full-screen container with the app background; pads for the status bar unless a header is shown. */
export function Screen({ children, style, topInset = true }: { children: ReactNode; style?: StyleProp<ViewStyle>; topInset?: boolean }) {
  const insets = useSafeAreaInsets();
  return <View style={[{ flex: 1, backgroundColor: colors.bg, paddingTop: topInset ? insets.top : 0 }, style]}>{children}</View>;
}

export function Button({
  title,
  onPress,
  variant = "primary",
  disabled,
  loading,
  icon,
  small,
  style,
}: {
  title: string;
  onPress: () => void;
  variant?: "primary" | "secondary" | "ghost" | "danger";
  disabled?: boolean;
  loading?: boolean;
  icon?: IconName;
  small?: boolean;
  style?: StyleProp<ViewStyle>;
}) {
  const bg = variant === "primary" ? colors.primary : variant === "secondary" ? colors.surface : "transparent";
  const fg = variant === "danger" ? colors.danger : variant === "ghost" ? colors.muted : colors.primaryFg;
  const off = disabled || loading;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={title}
      accessibilityState={{ disabled: !!off }}
      onPress={onPress}
      disabled={off}
      style={({ pressed }) => [
        {
          backgroundColor: bg,
          borderRadius: radius.md,
          paddingHorizontal: small ? 12 : 18,
          paddingVertical: small ? 7 : 12,
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
          opacity: off ? 0.5 : pressed ? 0.85 : 1,
          borderWidth: variant === "secondary" ? 1 : 0,
          borderColor: colors.line,
          minHeight: small ? 34 : 46,
        },
        style,
      ]}
    >
      {loading ? <ActivityIndicator size="small" color={fg} /> : icon ? <Ionicons name={icon} size={small ? 15 : 18} color={fg} /> : null}
      <Text style={{ color: fg, fontWeight: "600", fontSize: small ? 13 : 15 }}>{title}</Text>
    </Pressable>
  );
}

export function Card({ children, style }: { children: ReactNode; style?: StyleProp<ViewStyle> }) {
  return <View style={[{ backgroundColor: colors.surface, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.lineSoft }, style]}>{children}</View>;
}

/** A card with a colored icon + title, like "Your Knowledge" in the product design. */
export function SectionCard({ title, icon, count, children, style }: { title: string; icon: IconName; count?: number; children: ReactNode; style?: StyleProp<ViewStyle> }) {
  return (
    <View style={[{ backgroundColor: colors.knowledge, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.knowledgeLine, padding: space.lg }, style]}>
      <View style={{ flexDirection: "row", alignItems: "center", gap: 10, marginBottom: space.sm }}>
        <View style={{ width: 26, height: 26, borderRadius: 7, backgroundColor: "rgba(63,214,160,0.2)", alignItems: "center", justifyContent: "center" }}>
          <Ionicons name={icon} size={15} color={colors.green} />
        </View>
        <Text style={{ color: colors.green, fontSize: 17, fontWeight: "600" }}>{title}</Text>
        {count !== undefined && <Text style={{ color: colors.muted, fontSize: 13 }}>{count}</Text>}
      </View>
      {children}
    </View>
  );
}

export function Pill({ label, active, onPress, icon }: { label: string; active?: boolean; onPress: () => void; icon?: IconName }) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ selected: !!active }}
      onPress={onPress}
      style={{
        flexDirection: "row",
        alignItems: "center",
        gap: 6,
        paddingHorizontal: 14,
        paddingVertical: 7,
        borderRadius: radius.pill,
        backgroundColor: active ? colors.primary : colors.surface,
        borderWidth: 1,
        borderColor: active ? "transparent" : colors.lineSoft,
      }}
    >
      {icon && <Ionicons name={icon} size={14} color={active ? colors.primaryFg : colors.muted} />}
      <Text style={{ color: active ? colors.primaryFg : colors.muted, fontWeight: "600", fontSize: 13 }}>{label}</Text>
    </Pressable>
  );
}

const TYPE_STYLE: Record<string, { bg: string; label: string }> = {
  pdf: { bg: "#e5484d", label: "PDF" },
  docx: { bg: "#2f74b4", label: "DOC" },
  md: { bg: "#6b52d6", label: "MD" },
  txt: { bg: "#5c7087", label: "TXT" },
};

/** Colored file-type tile (red PDF, blue Word, ...). */
export function FileTag({ filename, size = 36 }: { filename: string; size?: number }) {
  const ext = fileExtension(filename);
  const t = TYPE_STYLE[ext] ?? { bg: "#5c7087", label: (ext || "FILE").slice(0, 4).toUpperCase() };
  return (
    <View accessibilityLabel={`${t.label} file`} style={{ width: size, height: size, borderRadius: 9, backgroundColor: t.bg, alignItems: "center", justifyContent: "center" }}>
      <Text style={{ color: "#fff", fontWeight: "800", fontSize: size > 40 ? 12 : 10 }}>{t.label}</Text>
    </View>
  );
}

const STATUS: Record<DocumentStatus, { label: string; color: string }> = {
  UPLOADING: { label: "Uploading", color: colors.warn },
  PROCESSING: { label: "Reading", color: colors.warn },
  INDEXING: { label: "Indexing", color: colors.warn },
  READY: { label: "Ready", color: colors.ok },
  FAILED: { label: "Failed", color: colors.danger },
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  const s = STATUS[status];
  return (
    <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
      <View style={{ width: 6, height: 6, borderRadius: 3, backgroundColor: s.color }} />
      <Text style={{ color: s.color, fontSize: 12.5, fontWeight: "600" }}>{s.label}</Text>
    </View>
  );
}

export function ErrorNote({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <View accessibilityRole="alert" style={{ backgroundColor: "rgba(255,138,122,0.1)", borderColor: "rgba(255,138,122,0.4)", borderWidth: 1, borderRadius: radius.md, padding: space.md, gap: 8 }}>
      <Text style={{ color: colors.fg, fontSize: 14 }}>{message}</Text>
      {onRetry && <Button title="Try again" onPress={onRetry} variant="secondary" small style={{ alignSelf: "flex-start" }} />}
    </View>
  );
}

export function EmptyState({ title, body, action }: { title: string; body?: string; action?: ReactNode }) {
  return (
    <View style={{ paddingVertical: space.xl, gap: 8, alignItems: "flex-start" }}>
      <EmberMark size={32} />
      <Text style={{ color: colors.fg, fontSize: 20, fontWeight: "700", marginTop: 4 }}>{title}</Text>
      {body && <Text style={{ color: colors.muted, fontSize: 15, lineHeight: 22 }}>{body}</Text>}
      {action && <View style={{ marginTop: 8 }}>{action}</View>}
    </View>
  );
}

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <View style={{ flexDirection: "row", alignItems: "center", gap: 10, paddingVertical: space.xl }} accessibilityRole="progressbar" accessibilityLabel={label}>
      <ActivityIndicator color={colors.ember} />
      <Text style={{ color: colors.muted }}>{label}</Text>
    </View>
  );
}

export function ScreenTitle({ title, subtitle, style }: { title: string; subtitle?: string; style?: StyleProp<TextStyle> }) {
  return (
    <View style={{ marginBottom: space.lg }}>
      <Text accessibilityRole="header" style={[{ color: colors.fg, fontSize: 28, fontWeight: "700", letterSpacing: -0.5 }, style]}>
        {title}
      </Text>
      {subtitle && <Text style={{ color: colors.muted, fontSize: 15, marginTop: 4 }}>{subtitle}</Text>}
    </View>
  );
}

export const hairline = StyleSheet.hairlineWidth;

import { Ionicons } from "@expo/vector-icons";
import { useEffect, useState } from "react";
import { Pressable, Text, TextInput, View } from "react-native";
import { searchService } from "@/services/search";
import { colors, radius } from "@/theme";

function useDebounced<T>(value: T, ms: number): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

/** Search field with debounced prefix autocomplete on the last word. */
export function SearchInput({
  workspaceId,
  initialValue = "",
  onSubmit,
  hero,
  autoFocus,
  placeholder = "Search your knowledge…",
}: {
  workspaceId: string | null;
  initialValue?: string;
  onSubmit: (q: string) => void;
  hero?: boolean;
  autoFocus?: boolean;
  placeholder?: string;
}) {
  const [value, setValue] = useState(initialValue);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [focused, setFocused] = useState(false);

  useEffect(() => setValue(initialValue), [initialValue]);

  const debounced = useDebounced(value, 180);
  const lastWord = debounced.split(/\s+/).pop() ?? "";

  useEffect(() => {
    if (!workspaceId || lastWord.length < 2 || lastWord.startsWith('"')) {
      setSuggestions([]);
      return;
    }
    const ctrl = new AbortController();
    searchService
      .autocomplete(workspaceId, lastWord, ctrl.signal)
      .then((s) => setSuggestions(s.filter((x) => x !== lastWord.toLowerCase())))
      .catch(() => setSuggestions([])); // best effort: never blocks searching
    return () => ctrl.abort();
  }, [workspaceId, lastWord]);

  const submit = (q: string) => {
    const t = q.trim();
    if (!t) return;
    setSuggestions([]);
    onSubmit(t);
  };

  const apply = (s: string) => {
    const words = value.split(/\s+/);
    words[words.length - 1] = s;
    const next = words.join(" ");
    setValue(next);
    submit(next);
  };

  return (
    <View>
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          gap: 10,
          paddingHorizontal: 16,
          height: hero ? 54 : 48,
          borderRadius: hero ? radius.pill : radius.lg,
          backgroundColor: hero ? "rgba(11,22,35,0.72)" : colors.sunken,
          borderWidth: 1,
          borderColor: focused ? colors.web : hero ? "rgba(255,255,255,0.14)" : colors.line,
        }}
      >
        <Ionicons name="search" size={19} color={hero ? "rgba(255,255,255,0.7)" : colors.muted} />
        <TextInput
          value={value}
          onChangeText={setValue}
          onSubmitEditing={() => submit(value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          autoFocus={autoFocus}
          placeholder={placeholder}
          placeholderTextColor={hero ? "rgba(255,255,255,0.55)" : colors.faint}
          returnKeyType="search"
          autoCapitalize="none"
          autoCorrect={false}
          accessibilityLabel="Search your documents"
          style={{ flex: 1, color: hero ? "#fff" : colors.fg, fontSize: 16, paddingVertical: 0, outlineStyle: "none" } as object}
        />
        {value.length > 0 && (
          <Pressable accessibilityLabel="Clear search" onPress={() => { setValue(""); setSuggestions([]); }} hitSlop={10}>
            <Ionicons name="close-circle" size={18} color={colors.faint} />
          </Pressable>
        )}
      </View>
      {focused && suggestions.length > 0 && (
        <View style={{ marginTop: 6, backgroundColor: colors.surface, borderRadius: radius.md, borderWidth: 1, borderColor: colors.line, overflow: "hidden" }}>
          {suggestions.map((s) => (
            <Pressable key={s} onPress={() => apply(s)} style={({ pressed }) => ({ paddingHorizontal: 14, paddingVertical: 12, backgroundColor: pressed ? colors.sunken : "transparent" })}>
              <Text style={{ color: colors.fg, fontSize: 15 }}>
                <Text style={{ fontWeight: "700" }}>{s.slice(0, lastWord.length)}</Text>
                <Text style={{ color: colors.muted }}>{s.slice(lastWord.length)}</Text>
              </Text>
            </Pressable>
          ))}
        </View>
      )}
    </View>
  );
}

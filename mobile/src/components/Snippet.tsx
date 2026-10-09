import { Text, type StyleProp, type TextStyle } from "react-native";
import { parseSnippet } from "@/lib/highlight";
import { colors } from "@/theme";

/** Renders a backend snippet ("...**term**...") with matched words glowing like embers. */
export function Snippet({ snippet, style }: { snippet: string; style?: StyleProp<TextStyle> }) {
  if (!snippet) return <Text style={[{ color: colors.muted, fontStyle: "italic" }, style]}>No preview available</Text>;
  return (
    <Text style={style}>
      {parseSnippet(snippet).map((p, i) =>
        p.hit ? (
          <Text key={i} style={{ backgroundColor: "rgba(255,122,47,0.42)", color: "#fff", fontWeight: "700" }}>
            {p.text}
          </Text>
        ) : (
          <Text key={i}>{p.text}</Text>
        ),
      )}
    </Text>
  );
}

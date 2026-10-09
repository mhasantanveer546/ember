import { useId } from "react";
import { Text, View } from "react-native";
import Svg, { Defs, LinearGradient, Path, Stop } from "react-native-svg";
import { colors } from "@/theme";

/** The flame: orange gradient body with a dark hollow core. */
export function EmberMark({ size = 28 }: { size?: number }) {
  const gid = `flame-${useId().replace(/[^a-zA-Z0-9]/g, "")}`;
  // Wrapped in a View: on web the raw <svg> is position:static, so an absolutely
  // positioned sibling (the hero art) would otherwise paint over it.
  return (
    <View style={{ width: size, height: size }} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
    <Svg width={size} height={size} viewBox="0 0 24 24">
      <Defs>
        <LinearGradient id={gid} x1="0.5" y1="0" x2="0.5" y2="1">
          <Stop offset="0" stopColor="#ffb457" />
          <Stop offset="0.55" stopColor="#ff7a2f" />
          <Stop offset="1" stopColor="#f2411d" />
        </LinearGradient>
      </Defs>
      <Path d="M12 2c.4 3 3.2 4.8 4.6 7.4 1 1.8 1.4 3.6 1.4 5.1a6 6 0 0 1-12 0c0-1.8.7-3.4 1.7-4.7.4 1.3 1.1 2.1 2 2.5C9 9.3 9.9 5 12 2Z" fill={`url(#${gid})`} />
      <Path d="M12 13c1.6 1.5 2.5 2.6 2.5 3.9a2.5 2.5 0 0 1-5 0c0-1.3.9-2.4 2.5-3.9Z" fill="#4a1406" fillOpacity={0.8} />
    </Svg>
    </View>
  );
}

export function Wordmark({ size = 22 }: { size?: number }) {
  return (
    <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
      <EmberMark size={size + 6} />
      <Text style={{ color: colors.fg, fontSize: size, fontWeight: "700", letterSpacing: -0.3 }}>Ember</Text>
    </View>
  );
}

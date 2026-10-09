import { Ionicons } from "@expo/vector-icons";
import { Tabs } from "expo-router";
import type { ColorValue } from "react-native";
import { colors } from "@/theme";

type Name = keyof typeof Ionicons.glyphMap;
const icon = (active: Name, inactive: Name) =>
  function TabIcon({ color, focused, size }: { color: ColorValue; focused: boolean; size: number }) {
    return <Ionicons name={focused ? active : inactive} size={size} color={color} />;
  };

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.web,
        tabBarInactiveTintColor: colors.muted,
        tabBarStyle: { backgroundColor: colors.sidebar, borderTopColor: colors.lineSoft },
        tabBarLabelStyle: { fontSize: 11, fontWeight: "600" },
        sceneStyle: { backgroundColor: colors.bg },
      }}
    >
      <Tabs.Screen name="index" options={{ title: "Home", tabBarIcon: icon("home", "home-outline") }} />
      <Tabs.Screen name="search" options={{ title: "Search", tabBarIcon: icon("search", "search-outline") }} />
      <Tabs.Screen name="knowledge" options={{ title: "Knowledge", tabBarIcon: icon("document-text", "document-text-outline") }} />
      <Tabs.Screen name="profile" options={{ title: "Profile", tabBarIcon: icon("person", "person-outline") }} />
    </Tabs>
  );
}

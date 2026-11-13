# PERIMETER Proguard Rules
-keepattributes *Annotation*
-keepclassmembers class * {
    @com.google.gson.annotations.SerializedName <fields>;
}
-keep class org.perimeter.safety.data.model.** { *; }


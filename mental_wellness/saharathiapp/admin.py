from django.contrib import admin
from .models import ChatSession, Message

# 🔹 Inline messages inside ChatSession
class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'short_text', 'timestamp', 'is_read')
    can_delete = False
    show_change_link = False
    classes = ['collapse']  # Collapsible section

    def short_text(self, obj):
        return obj.text[:80] + ("..." if len(obj.text) > 80 else "")
    short_text.short_description = "Message Preview"


# 🔹 ChatSession Admin
@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'session_id', 'created_at', 'last_activity', 'message_count', 'is_active')
    search_fields = ('title', 'messages__text')
    ordering = ('-last_activity', '-created_at')
    list_filter = ('created_at', 'is_active')
    inlines = [MessageInline]
    actions = ['mark_inactive', 'mark_active']

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = "Messages"

    # 🔹 Admin actions to archive/unarchive
    @admin.action(description="Mark selected sessions as inactive")
    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description="Mark selected sessions as active")
    def mark_active(self, request, queryset):
        queryset.update(is_active=True)


# 🔹 Message Admin
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'session', 'short_text', 'timestamp', 'is_read')
    list_filter = ('sender', 'timestamp', 'is_read')
    search_fields = ('text', 'session__title')
    ordering = ('-timestamp',)

    def short_text(self, obj):
        return obj.text[:100] + ("..." if len(obj.text) > 100 else "")
    short_text.short_description = "Preview"

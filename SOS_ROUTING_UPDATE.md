# SOS routing and reliability fixes

- Every citizen SOS is now persisted as an `SOS_ALERT` community feed post.
- SOS WebSocket events are broadcast to police, volunteers, and admins.
- Admin dashboard now has a live citizen SOS alert panel plus polling fallback.
- Police dashboard explicitly requests browser notification permission and keeps polling as a fallback.
- Police/volunteer/admin can see the same active SOS records; severity is used for priority, not visibility.
- Responder accept and SOS resolve endpoints now require authenticated responder/admin accounts.
- Existing database records are not deleted.

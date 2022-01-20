from rest_framework import permissions


class IsAdminOrUserOwnSubscriptions(permissions.BasePermission):
    """
    Custom permission to only allow admins to view/modify subscriptions for all users,
    or users to view/modify only own subscriptions.
    """

    def has_permission(self, request, view):
        if request.user.is_admin:
            return True

        return view.kwargs.get('follower_id') == request.user.pk

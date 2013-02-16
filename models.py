

class User(object):
    """
    This provides default implementations for the methods that Flask-Login
    expects user objects to have.
    """
    def is_active(self):
        """
        Returns `True`.
        """
        return True

    def is_authenticated(self):
        """
        Returns `True`.
        """
        return True

    def is_anonymous(self):
        """
        Returns `False`.
        """
        return False

    def get_id(self):
        """
        Assuming that the user object has an `id` attribute, this will take
        that and convert it to `unicode`.
        """
        try:
            return unicode(self.id)
        except AttributeError:
            raise NotImplementedError("No `id` attribute - override get_id")

    def __eq__(self, other):
        """
        Checks the equality of two `UserMixin` objects using `get_id`.
        """
        if isinstance(other, UserMixin):
            return self.get_id() == other.get_id()
        return NotImplemented

    def __ne__(self, other):
        """
        Checks the inequality of two `UserMixin` objects using `get_id`.
        """
        equal = self.__eq__(other)
        if equal is NotImplemented:
            return NotImplemented
        return not equal
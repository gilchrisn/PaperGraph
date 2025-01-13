from collections import deque
import heapq

class Queue:
    def __init__(self):
        self.queue = deque()

    def insert(self, element):
        """Insert an element into the queue."""
        self.queue.append(element)

    def pop(self):
        """Remove and return the first element from the queue."""
        if self.is_empty():
            raise IndexError("Pop from an empty queue")
        return self.queue.popleft()

    def is_empty(self):
        """Check if the queue is empty."""
        return len(self.queue) == 0

    def __len__(self):
        """Return the size of the queue."""
        return len(self.queue)
    
class Stack:
    def __init__(self):
        self.stack = []

    def insert(self, element):
        """Insert an element into the stack."""
        self.stack.append(element)

    def pop(self):
        """Remove and return the last element from the stack."""
        if self.is_empty():
            raise IndexError("Pop from an empty stack")
        return self.stack.pop()

    def is_empty(self):
        """Check if the stack is empty."""
        return len(self.stack) == 0

    def __len__(self):
        """Return the size of the stack."""
        return len(self.stack)

class PriorityQueue:
    def __init__(self, comparator=None):
        """
        Initialize a priority queue.

        :param comparator: A function defining the priority. Higher priority elements should have lower values.
                           Example: For sorting by similarity score in descending order:
                           comparator = lambda x: -x['similarity_score']
        """
        self.heap = []
        self.comparator = comparator if comparator else lambda x: x  # Default comparator is identity function

    def insert(self, element):
        """Insert an element into the priority queue."""
        heapq.heappush(self.heap, (self.comparator(element), element))

    def pop(self):
        """Remove and return the highest-priority element."""
        if self.is_empty():
            raise IndexError("Pop from an empty priority queue")
        return heapq.heappop(self.heap)[1]

    def is_empty(self):
        """Check if the priority queue is empty."""
        return len(self.heap) == 0

    def __len__(self):
        """Return the size of the priority queue."""
        return len(self.heap)


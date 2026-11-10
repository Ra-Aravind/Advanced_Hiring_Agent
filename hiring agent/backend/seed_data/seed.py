"""
Seed 210+ questions (30 per technology × 7 technologies).
Run: python -m seed_data.seed
"""
import asyncio
import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal, create_tables
from app.models.technology import Technology
from app.models.question import Question
from sqlalchemy import select
from app.main import _seed_initial_data


# ──────────────────────────────────────────────────────────────
# QUESTION BANK
# ──────────────────────────────────────────────────────────────

def q(qtype, difficulty, text, options=None, correct=None, explanation=None, tags=None):
    return {
        "question_type": qtype,
        "difficulty": difficulty,
        "question_text": text,
        "options": options,
        "correct_answer": correct,
        "explanation": explanation or "",
        "tags": tags or [],
        "max_score": 10,
        "source": "manual",
    }

def mcq(difficulty, text, a, b, c, d, correct_idx, explanation=None, tags=None):
    if isinstance(explanation, list):
        tags = explanation
        explanation = None
    options = [
        {"label": "A", "text": a, "is_correct": correct_idx == 0},
        {"label": "B", "text": b, "is_correct": correct_idx == 1},
        {"label": "C", "text": c, "is_correct": correct_idx == 2},
        {"label": "D", "text": d, "is_correct": correct_idx == 3},
    ]
    correct_text = [a, b, c, d][correct_idx]
    return q("mcq", difficulty, text, options, correct_text, explanation, tags)

def sa(difficulty, text, correct, explanation=None, tags=None):
    if isinstance(explanation, list):
        tags = explanation
        explanation = None
    return q("short_answer", difficulty, text, None, correct, explanation, tags)

def code_q(difficulty, text, correct, explanation=None, tags=None):
    if isinstance(explanation, list):
        tags = explanation
        explanation = None
    return q("code", difficulty, text, None, correct, explanation, tags)


# ─── PYTHON ───────────────────────────────────────────────────
PYTHON_QUESTIONS = [
    # BEGINNER (10)
    mcq("beginner","What is the output of `print(type([]))`?","<class 'list'>","<class 'tuple'>","<class 'dict'>","<class 'set'>",0,"The type of an empty list literal is <class 'list'>.",["types","basics"]),
    mcq("beginner","Which keyword is used to define a function in Python?","func","define","def","function",2,"Python uses 'def' to define functions.",["functions","syntax"]),
    mcq("beginner","What does `len('hello')` return?","4","5","6","Error",1,"'hello' has 5 characters.",["strings","builtins"]),
    mcq("beginner","Which of the following is a mutable data type in Python?","str","tuple","list","int",2,"Lists are mutable; strings, tuples, and ints are immutable.",["data-types"]),
    mcq("beginner","What is the output of `2 ** 3`?","6","8","9","5",1,"** is the exponentiation operator. 2^3 = 8.",["operators"]),
    mcq("beginner","How do you create a comment in Python?","// comment","# comment","/* comment */","-- comment",1,"Python single-line comments start with #.",["syntax"]),
    mcq("beginner","What does `range(5)` produce?","[1,2,3,4,5]","[0,1,2,3,4]","[0,1,2,3,4,5]","(0,1,2,3,4)",1,"range(5) generates 0 to 4 inclusive.",["loops","builtins"]),
    mcq("beginner","Which method adds an element to the end of a list?","add()","insert()","append()","push()",2,"list.append(x) adds x to the end of the list.",["lists","methods"]),
    sa("beginner","What is the difference between a list and a tuple in Python?","A list is mutable (can be changed after creation) and uses square brackets []. A tuple is immutable (cannot be changed) and uses parentheses (). Lists are slower but more flexible; tuples are faster and used for fixed data.",["lists","tuples"]),
    sa("beginner","How do you open and read a file in Python?","Use the open() function with mode 'r': with open('file.txt', 'r') as f: content = f.read(). The 'with' statement ensures the file is properly closed after use.",["files","io"]),

    # INTERMEDIATE (10)
    mcq("intermediate","What is the output of `[x**2 for x in range(4)]`?","[0,1,4,9]","[1,4,9,16]","[0,1,2,3]","[1,2,3,4]",0,"List comprehension squares 0,1,2,3 giving [0,1,4,9].",["comprehensions","lists"]),
    mcq("intermediate","What does the `*args` parameter do in a function definition?","Accepts keyword arguments","Accepts unlimited positional arguments","Unpacks a list","Creates a tuple argument",1,"*args collects extra positional arguments into a tuple.",["functions","args"]),
    mcq("intermediate","Which module provides high-performance alternatives to built-in containers?","sys","os","collections","itertools",2,"The collections module provides namedtuple, deque, Counter, etc.",["modules","collections"]),
    mcq("intermediate","What is a decorator in Python?","A way to add CSS to Python","A function that modifies another function","A class attribute","A type of loop",1,"Decorators wrap functions to modify or extend their behavior using @syntax.",["decorators","functions"]),
    mcq("intermediate","What does `dict.get('key', default)` do?","Raises KeyError if missing","Returns default if key missing","Inserts default if missing","Returns None always",1,"dict.get() returns the value for key if it exists, else the default.",["dict","methods"]),
    mcq("intermediate","What is the GIL in Python?","Global Import Lock","Global Interpreter Lock","General Input Library","Generalized Instance Loop",1,"The GIL (Global Interpreter Lock) prevents multiple threads from executing Python bytecode simultaneously.",["threading","advanced"]),
    sa("intermediate","Explain the difference between `__str__` and `__repr__` in Python.","__str__ is called by str() and print() for a human-readable string representation. __repr__ is called by repr() and is meant to be an unambiguous, developer-facing representation that ideally could recreate the object. If __str__ is not defined, Python falls back to __repr__.",["dunder","oop"]),
    sa("intermediate","What are Python generators and when would you use them?","Generators are functions that use 'yield' to return values one at a time, creating an iterator. They are memory-efficient because they generate values on-demand rather than storing all in memory. Use them for large datasets, infinite sequences, or pipelines.",["generators","memory"]),
    code_q("intermediate","Write a Python function to check if a string is a palindrome.",
        "def is_palindrome(s):\n    s = s.lower().replace(' ', '')\n    return s == s[::-1]",
        "Normalize the string, then compare it to its reverse using slicing [::-1].",["strings","algorithms"]),
    code_q("intermediate","Write a Python function to count the frequency of each character in a string using collections.Counter.",
        "from collections import Counter\n\ndef char_frequency(s):\n    return dict(Counter(s))",
        "Counter returns a dictionary-like object with character frequencies.",["collections","strings"]),

    # ADVANCED (10)
    mcq("advanced","Which of the following correctly describes Python's memory management?","Manual malloc/free","Reference counting + cyclic GC","Stack-only allocation","OS-managed only",1,"Python uses reference counting as primary memory management, supplemented by a cyclic garbage collector.",["memory","internals"]),
    mcq("advanced","What is the output of `(lambda x: x*2)(5)`?","5","10","25","Error",1,"Immediately invoked lambda: (lambda x: x*2)(5) = 5*2 = 10.",["lambda","functional"]),
    mcq("advanced","What does `functools.lru_cache` do?","Limits function recursion","Caches function return values","Lazy-loads modules","Logs function calls",1,"lru_cache memoizes results of expensive function calls using a least-recently-used cache.",["functools","caching"]),
    mcq("advanced","Which statement about Python's `asyncio` is TRUE?","It uses multiple OS threads","It requires C extensions","It enables concurrent I/O with a single thread","It replaces multiprocessing",2,"asyncio enables concurrent I/O-bound operations using cooperative multitasking in a single thread.",["asyncio","concurrency"]),
    mcq("advanced","What is a metaclass in Python?","A class that cannot be instantiated","The class of a class","A decorator for classes","An abstract base class",1,"A metaclass is the class whose instances are classes themselves. 'type' is the default metaclass.",["metaclass","oop"]),
    sa("advanced","Explain Python's descriptor protocol with an example.",
        "The descriptor protocol allows objects to customize attribute access via __get__, __set__, and __delete__ methods. When you access obj.attr, Python checks if the class attribute is a descriptor. Properties use this: @property calls __get__. Example: class Celsius: def __get__(self, obj, type=None): return obj._temp * 9/5 + 32",["descriptors","oop"]),
    sa("advanced","What are Python's __slots__ and when should you use them?",
        "__slots__ restricts instance attribute creation to a fixed set, preventing __dict__ creation per instance. Use them when creating many instances of a class to save memory (40-50% reduction) and speed up attribute access. Define as: __slots__ = ['x', 'y']",["memory","optimization"]),
    code_q("advanced","Implement a thread-safe singleton pattern in Python.",
        "import threading\n\nclass Singleton:\n    _instance = None\n    _lock = threading.Lock()\n\n    def __new__(cls):\n        if cls._instance is None:\n            with cls._lock:\n                if cls._instance is None:\n                    cls._instance = super().__new__(cls)\n        return cls._instance",
        "Use double-checked locking to prevent race conditions while keeping performance.",["design-patterns","threading"]),
    code_q("advanced","Write a context manager using both __enter__ and __exit__ for timing code execution.",
        "import time\n\nclass Timer:\n    def __enter__(self):\n        self.start = time.perf_counter()\n        return self\n\n    def __exit__(self, *args):\n        self.elapsed = time.perf_counter() - self.start\n        print(f'Elapsed: {self.elapsed:.4f}s')\n\n# Usage:\nwith Timer() as t:\n    sum(range(1000000))",
        "Context managers use __enter__ to set up and __exit__ to tear down resources, even on exceptions.",["context-managers","performance"]),
    code_q("advanced","Implement a simple LRU Cache from scratch using OrderedDict.",
        "from collections import OrderedDict\n\nclass LRUCache:\n    def __init__(self, capacity):\n        self.cache = OrderedDict()\n        self.capacity = capacity\n\n    def get(self, key):\n        if key not in self.cache:\n            return -1\n        self.cache.move_to_end(key)\n        return self.cache[key]\n\n    def put(self, key, value):\n        if key in self.cache:\n            self.cache.move_to_end(key)\n        self.cache[key] = value\n        if len(self.cache) > self.capacity:\n            self.cache.popitem(last=False)",
        "OrderedDict maintains insertion order. move_to_end marks recently used; popitem(last=False) removes LRU.",["data-structures","caching"]),
]

# ─── JAVA ─────────────────────────────────────────────────────
JAVA_QUESTIONS = [
    mcq("beginner","Which keyword is used to inherit a class in Java?","implements","inherits","extends","super",2,"Java uses 'extends' for class inheritance.",["oop","inheritance"]),
    mcq("beginner","What is the default value of an int in Java?","null","0","1","-1",1,"Primitive int fields default to 0 in Java.",["primitives","defaults"]),
    mcq("beginner","Which of these is NOT a Java primitive type?","int","String","boolean","char",1,"String is a class (reference type), not a primitive.",["types","primitives"]),
    mcq("beginner","What does JVM stand for?","Java Variable Manager","Java Virtual Machine","Java Verified Method","Java Version Manager",1,"The JVM executes Java bytecode and provides platform independence.",["jvm","basics"]),
    mcq("beginner","How do you declare a constant in Java?","const int X=5","static final int X=5","final static X=5","constant int X=5",1,"Java uses 'static final' for constants.",["constants","syntax"]),
    mcq("beginner","Which method is the entry point of a Java program?","start()","run()","main()","init()",2,"public static void main(String[] args) is the entry point.",["basics","main"]),
    mcq("beginner","What is the size of a long in Java?","32 bits","64 bits","16 bits","128 bits",1,"long is a 64-bit signed integer in Java.",["primitives","types"]),
    sa("beginner","What is the difference between == and .equals() in Java?","== compares object references (memory addresses) for objects and values for primitives. .equals() compares the content/value of objects. For String comparison, always use .equals() because == may return false even for strings with the same content if they are different objects in memory.",["strings","comparison"]),
    sa("beginner","What is autoboxing in Java?","Autoboxing is the automatic conversion of primitive types (int, double, etc.) to their corresponding wrapper class objects (Integer, Double, etc.) and vice versa (unboxing). For example: Integer i = 5; automatically boxes the int 5.",["generics","types"]),
    sa("beginner","Explain the difference between ArrayList and LinkedList in Java.",
        "ArrayList uses a dynamic array internally, offering O(1) random access but O(n) for insertion/deletion in the middle. LinkedList uses a doubly-linked list, offering O(1) insertion/deletion at head/tail but O(n) random access. Use ArrayList for frequent reads, LinkedList for frequent insertions/deletions.",["collections","data-structures"]),

    mcq("intermediate","What is the output of `System.out.println(10 + 20 + \"30\")`?","102030","3030","10 + 20 + 30","Error",1,"Left to right: 10+20=30, then 30+\"30\"=\"3030\".",["operators","strings"]),
    mcq("intermediate","Which interface must be implemented to use an object in a for-each loop?","Iterable","Iterator","Collection","Comparable",0,"Implementing Iterable<T> with iterator() enables for-each.",["collections","iteration"]),
    mcq("intermediate","What does the `volatile` keyword guarantee?","Thread synchronization","Visibility of changes across threads","Atomicity","Immutability",1,"volatile ensures all threads see the latest value, preventing caching.",["concurrency","threading"]),
    mcq("intermediate","Which design pattern does `java.util.Iterator` implement?","Factory","Observer","Iterator","Strategy",2,"Iterator pattern provides a way to access elements sequentially without exposing the underlying structure.",["design-patterns"]),
    mcq("intermediate","What is the purpose of the `transient` keyword?","Makes a variable thread-safe","Excludes a field from serialization","Creates a temporary variable","Marks a method as deprecated",1,"transient prevents a field from being serialized.",["serialization"]),
    sa("intermediate","Explain Java's HashMap internal working.",
        "HashMap uses an array of buckets. On put(key, value): key.hashCode() is computed, then (hash & (n-1)) finds the bucket index. If collision occurs (two keys map to same bucket), keys are stored in a linked list (or red-black tree if size > 8 in Java 8+). On get(key): same hash to find bucket, then .equals() to find the right entry.",["collections","hashing"]),
    sa("intermediate","What is the difference between checked and unchecked exceptions in Java?",
        "Checked exceptions (e.g., IOException, SQLException) must be declared with 'throws' or handled with try-catch at compile time. Unchecked exceptions (extend RuntimeException, e.g., NullPointerException, ArrayIndexOutOfBoundsException) do not need to be declared. Checked exceptions represent recoverable conditions; unchecked represent programming errors.",["exceptions","error-handling"]),
    code_q("intermediate","Write a Java method to reverse a string without using StringBuilder.reverse().",
        "public static String reverse(String s) {\n    char[] chars = s.toCharArray();\n    int left = 0, right = chars.length - 1;\n    while (left < right) {\n        char temp = chars[left];\n        chars[left++] = chars[right];\n        chars[right--] = temp;\n    }\n    return new String(chars);\n}",["strings","algorithms"]),
    code_q("intermediate","Implement a generic stack using Java generics.",
        "import java.util.ArrayList;\n\npublic class Stack<T> {\n    private ArrayList<T> items = new ArrayList<>();\n\n    public void push(T item) { items.add(item); }\n\n    public T pop() {\n        if (isEmpty()) throw new RuntimeException(\"Stack is empty\");\n        return items.remove(items.size() - 1);\n    }\n\n    public T peek() {\n        if (isEmpty()) throw new RuntimeException(\"Stack is empty\");\n        return items.get(items.size() - 1);\n    }\n\n    public boolean isEmpty() { return items.isEmpty(); }\n    public int size() { return items.size(); }\n}",["generics","data-structures"]),
    code_q("intermediate","Write a Java program to find the second largest element in an array.",
        "public static int secondLargest(int[] arr) {\n    if (arr.length < 2) throw new IllegalArgumentException(\"Need at least 2 elements\");\n    int first = Integer.MIN_VALUE, second = Integer.MIN_VALUE;\n    for (int num : arr) {\n        if (num > first) { second = first; first = num; }\n        else if (num > second && num != first) second = num;\n    }\n    if (second == Integer.MIN_VALUE) throw new RuntimeException(\"No second largest\");\n    return second;\n}",["arrays","algorithms"]),

    mcq("advanced","What is the purpose of Java's `CompletableFuture`?","Synchronous computation","Asynchronous, composable future operations","Thread pool management","Replace synchronized blocks",1,"CompletableFuture enables non-blocking async pipelines with thenApply, thenCompose, etc.",["concurrency","async"]),
    mcq("advanced","Which garbage collection algorithm is used by G1GC?","Mark-Sweep","Generational region-based collection","Reference counting","Shenandoah",1,"G1GC divides heap into regions and collects the most garbage-dense ones first.",["gc","jvm"]),
    mcq("advanced","What is a functional interface in Java?","An interface with no methods","An interface with exactly one abstract method","An interface that extends Function","Any interface with default methods",1,"Functional interfaces have exactly one abstract method and can be used with lambdas.",["functional","lambdas"]),
    mcq("advanced","What does the `@FunctionalInterface` annotation do?","Generates boilerplate code","Enforces single abstract method at compile time","Enables serialization","Marks the interface as deprecated",1,"@FunctionalInterface causes a compile error if you accidentally add more than one abstract method.",["annotations","functional"]),
    sa("advanced","Explain the Java Memory Model and happens-before relationship.",
        "The JMM defines how threads interact through memory. A happens-before (HB) relationship guarantees that if action A HB action B, then A's effects are visible to B. Examples: volatile write HB volatile read; monitor unlock HB subsequent lock; thread.start() HB any action in the thread. Without HB, the JVM/CPU may reorder operations for optimization.",["concurrency","memory-model"]),
    code_q("advanced","Implement a thread-safe singleton using double-checked locking.",
        "public class Singleton {\n    private static volatile Singleton instance;\n\n    private Singleton() {}\n\n    public static Singleton getInstance() {\n        if (instance == null) {\n            synchronized (Singleton.class) {\n                if (instance == null) {\n                    instance = new Singleton();\n                }\n            }\n        }\n        return instance;\n    }\n}",["design-patterns","threading"]),
    code_q("advanced","Write a Java Stream API solution to find the top 3 most frequent words in a list.",
        "import java.util.*;\nimport java.util.stream.*;\n\npublic static List<String> top3Words(List<String> words) {\n    return words.stream()\n        .collect(Collectors.groupingBy(w -> w, Collectors.counting()))\n        .entrySet().stream()\n        .sorted(Map.Entry.<String, Long>comparingByValue().reversed())\n        .limit(3)\n        .map(Map.Entry::getKey)\n        .collect(Collectors.toList());\n}",["streams","collections"]),
    code_q("advanced","Implement a custom functional interface and use it with a method reference.",
        "@FunctionalInterface\ninterface StringTransformer {\n    String transform(String input);\n}\n\npublic class Demo {\n    public static String toUpperCase(String s) {\n        return s.toUpperCase();\n    }\n\n    public static void main(String[] args) {\n        StringTransformer transformer = Demo::toUpperCase;\n        System.out.println(transformer.transform(\"hello\")); // HELLO\n\n        // Lambda equivalent:\n        StringTransformer lower = s -> s.toLowerCase();\n        System.out.println(lower.transform(\"WORLD\")); // world\n    }\n}",["functional","lambdas","method-references"]),
    sa("advanced","What are Java's virtual threads (Project Loom) and how do they differ from platform threads?",
        "Virtual threads (Java 21) are lightweight threads managed by the JVM, not the OS. Platform threads are OS threads (expensive: ~1MB stack). Virtual threads use carrier threads from a fork-join pool and are parked/unparked when blocking I/O occurs. You can create millions of virtual threads cheaply. They enable simple synchronous-style code with the performance of async. Created with Thread.ofVirtual().start(runnable).",["concurrency","java21"]),
]

# ─── C ─────────────────────────────────────────────────────────
C_QUESTIONS = [
    mcq("beginner","What is the correct syntax to declare an integer variable in C?","integer x;","int x;","var x;","x: int;",1,"In C, integer variables are declared with the 'int' keyword.",["syntax","variables"]),
    mcq("beginner","Which symbol is used for pointer declaration?","&","*","@","#",1,"* is used to declare pointer variables in C.",["pointers","syntax"]),
    mcq("beginner","What does `printf(\"%d\", 42)` output?","42","d","42d","Error",0,"%d format specifier prints an integer.",["io","printf"]),
    mcq("beginner","Which header file is needed for `printf` and `scanf`?","stdlib.h","string.h","stdio.h","math.h",2,"stdio.h (Standard Input Output) provides printf, scanf, etc.",["headers","io"]),
    mcq("beginner","What is the size of `char` in C?","2 bytes","4 bytes","1 byte","8 bytes",2,"char is always 1 byte in C.",["types","sizes"]),
    mcq("beginner","What does `scanf(\"%d\", &x)` do?","Prints x","Reads an integer into x","Declares x","Compares x",1,"& gives the address of x so scanf can write to it.",["io","pointers"]),
    mcq("beginner","Which loop always executes at least once?","for","while","do-while","None of the above",2,"do-while checks the condition after executing the body.",["loops","control-flow"]),
    sa("beginner","What is the difference between `++i` (pre-increment) and `i++` (post-increment) in C?","Pre-increment (++i) increments the value of i and returns the new value. Post-increment (i++) returns the current value of i and then increments it. In a standalone statement they produce the same result, but in expressions like a = ++i vs a = i++, the difference matters.",["operators","basics"]),
    sa("beginner","Explain what a null terminator is in C strings.","In C, strings are character arrays terminated by a null character '\\0' (ASCII value 0). This tells functions like printf, strlen, and strcpy where the string ends. When declaring char str[] = \"hello\", the compiler automatically adds a '\\0' at position 5, making the array 6 bytes.",["strings","arrays"]),
    sa("beginner","What is the difference between `int a[5]` and `int *a` in C?","int a[5] allocates a fixed array of 5 integers on the stack. The name 'a' is a constant pointer to the first element. int *a is a pointer variable that can point to any integer or array, allocated on the heap with malloc. The pointer itself can be reassigned, but the array name cannot.",["arrays","pointers"]),

    mcq("intermediate","What does `malloc` return if memory allocation fails?","0","NULL","1","-1",1,"malloc returns NULL on failure, which must be checked.",["memory","malloc"]),
    mcq("intermediate","What is a dangling pointer?","A NULL pointer","A pointer to freed memory","An uninitialized pointer","A pointer to a pointer",1,"A dangling pointer points to memory that has been freed, causing undefined behavior if accessed.",["pointers","memory"]),
    mcq("intermediate","What is the output of `sizeof(int *)` on a 64-bit system?","4","8","2","Depends on int size",1,"On 64-bit systems, all pointers are 8 bytes regardless of what they point to.",["pointers","sizeof"]),
    mcq("intermediate","Which function is used to copy memory in C?","strcpy","memcpy","malloc","calloc",1,"memcpy copies n bytes from source to destination.",["memory","string"]),
    mcq("intermediate","What does `static` mean for a local variable?","Constant value","Persists across function calls","Thread-local storage","Invisible outside file",1,"A static local variable retains its value between function calls.",["storage-class","static"]),
    sa("intermediate","Explain the difference between `malloc`, `calloc`, and `realloc`.","malloc(size) allocates size bytes of uninitialized memory. calloc(n, size) allocates n*size bytes and initializes all to zero. realloc(ptr, new_size) resizes a previously allocated block, copying existing data. All return NULL on failure and must be freed with free().",["memory","allocation"]),
    sa("intermediate","What is a segmentation fault and what are common causes?","A segmentation fault (SIGSEGV) occurs when a program accesses memory it's not allowed to. Common causes: dereferencing NULL/dangling pointers, accessing array out of bounds, writing to read-only memory (string literals), stack overflow from deep recursion.",["memory","debugging"]),
    code_q("intermediate","Write a C function to reverse an array in-place.",
        "#include <stdio.h>\n\nvoid reverse_array(int *arr, int n) {\n    int left = 0, right = n - 1;\n    while (left < right) {\n        int temp = arr[left];\n        arr[left++] = arr[right];\n        arr[right--] = temp;\n    }\n}",["arrays","algorithms"]),
    code_q("intermediate","Write a C function to implement a stack using an array.",
        "#define MAX 100\n\ntypedef struct {\n    int data[MAX];\n    int top;\n} Stack;\n\nvoid init(Stack *s) { s->top = -1; }\n\nvoid push(Stack *s, int val) {\n    if (s->top == MAX-1) { printf(\"Overflow\\n\"); return; }\n    s->data[++s->top] = val;\n}\n\nint pop(Stack *s) {\n    if (s->top == -1) { printf(\"Underflow\\n\"); return -1; }\n    return s->data[s->top--];\n}",["data-structures","stack"]),
    code_q("intermediate","Write a C function to find if a linked list has a cycle using Floyd's algorithm.",
        "typedef struct Node { int val; struct Node *next; } Node;\n\nint has_cycle(Node *head) {\n    Node *slow = head, *fast = head;\n    while (fast && fast->next) {\n        slow = slow->next;\n        fast = fast->next->next;\n        if (slow == fast) return 1;\n    }\n    return 0;\n}",["linked-list","algorithms"]),

    mcq("advanced","What is the purpose of `volatile` in C?","Constant value","Prevents compiler optimization of the variable","Thread safety","Dynamic memory",1,"volatile tells the compiler the variable can change unexpectedly (e.g., hardware register, signal handler).",["keywords","optimization"]),
    mcq("advanced","What is undefined behavior (UB) in C?","A runtime error","Behavior not defined by the C standard","A compiler warning","A segfault",1,"UB means the C standard imposes no requirements. The compiler may do anything, including nasal demons.",["ub","standards"]),
    mcq("advanced","What does `restrict` keyword hint to the compiler?","No aliasing for the pointer","Read-only memory","Thread-local pointer","Volatile pointer",0,"restrict promises that no other pointer will alias the same memory, enabling optimizations.",["optimization","pointers"]),
    mcq("advanced","What is the difference between `struct` and `union` in C?","No difference","struct members share memory; union has separate memory","union members share memory; struct has separate memory","unions cannot have pointers",2,"A union allocates memory for the largest member; all members share that memory.",["struct","union"]),
    sa("advanced","Explain memory layout of a C program (text, data, BSS, heap, stack).",
        "Text segment: compiled code (read-only). Data segment: initialized global/static variables. BSS: uninitialized global/static variables (zeroed at startup). Heap: dynamic memory (malloc/free), grows upward. Stack: local variables, function call frames, grows downward. Stack and heap grow toward each other.",["memory","internals"]),
    code_q("advanced","Implement a generic swap function using void pointers in C.",
        "#include <string.h>\n\nvoid swap(void *a, void *b, size_t size) {\n    char temp[size];\n    memcpy(temp, a, size);\n    memcpy(a, b, size);\n    memcpy(b, temp, size);\n}\n\n// Usage: int x=1,y=2; swap(&x,&y,sizeof(int));",["pointers","generics"]),
    code_q("advanced","Implement a simple memory allocator using a free list.",
        "/* Simplified buddy-style allocator */\n#include <stddef.h>\n#include <string.h>\n\n#define HEAP_SIZE 4096\nstatic char heap[HEAP_SIZE];\n\ntypedef struct Block { size_t size; int free; struct Block *next; } Block;\nstatic Block *head = (Block*)heap;\n\nvoid init_allocator() {\n    head->size = HEAP_SIZE - sizeof(Block);\n    head->free = 1;\n    head->next = NULL;\n}\n\nvoid *my_malloc(size_t size) {\n    Block *curr = head;\n    while (curr) {\n        if (curr->free && curr->size >= size) {\n            curr->free = 0;\n            return (void*)(curr + 1);\n        }\n        curr = curr->next;\n    }\n    return NULL;\n}\n\nvoid my_free(void *ptr) {\n    Block *block = (Block*)ptr - 1;\n    block->free = 1;\n}",["memory","allocator","advanced"]),
    sa("advanced","What are the POSIX thread synchronization primitives and when would you use each?","Mutex (pthread_mutex_t): mutual exclusion for critical sections. Condition variable (pthread_cond_t): blocking until a condition is true (used with mutex). Read-write lock (pthread_rwlock_t): multiple concurrent readers, exclusive writer. Semaphore: counting resource access limit. Spinlock: busy-wait loop, for very short critical sections on multicore. Barrier: wait for all threads to reach a point.",["pthreads","concurrency"]),
    code_q("advanced","Write a C function for binary search on a sorted array.",
        "int binary_search(int *arr, int n, int target) {\n    int left = 0, right = n - 1;\n    while (left <= right) {\n        int mid = left + (right - left) / 2;\n        if (arr[mid] == target) return mid;\n        if (arr[mid] < target) left = mid + 1;\n        else right = mid - 1;\n    }\n    return -1; // not found\n}",["algorithms","searching"]),
]

# ─── C++ ──────────────────────────────────────────────────────
CPP_QUESTIONS = [
    mcq("beginner","Which operator is used to access class members through a pointer?",".",":","->","*",2,"The -> operator dereferences a pointer and accesses a member.",["pointers","syntax"]),
    mcq("beginner","What is the output of `cout << 5/2` in C++?","2.5","2","3","Error",1,"Integer division in C++ truncates: 5/2 = 2.",["operators","types"]),
    mcq("beginner","Which keyword is used to define a class in C++?","struct","class","object","type",1,"C++ uses 'class' to define classes.",["oop","syntax"]),
    mcq("beginner","What is the default access specifier for class members in C++?","public","protected","private","none",2,"Class members are private by default in C++ (struct members are public).",["oop","access"]),
    mcq("beginner","Which header provides `string` in C++?","<cstring>","<string>","<strings>","<str>",1,"#include <string> provides the std::string class.",["strings","headers"]),
    mcq("beginner","What is `std::endl`?","End of file","Newline + flush buffer","Delete line","Error handler",1,"std::endl outputs '\\n' and flushes the output buffer.",["io","streams"]),
    mcq("beginner","What is a constructor?","A function that destroys objects","A special function called when object is created","A static class method","A virtual function",1,"Constructors initialize objects when they are created, having the same name as the class.",["oop","constructors"]),
    sa("beginner","What is the difference between stack and heap memory allocation in C++?","Stack memory: automatically managed, fast, limited size. Local variables live here and are destroyed when scope ends. Heap memory: manually managed with new/delete, larger but slower. Used for dynamic objects. Stack overflow is possible if recursion is too deep. Heap fragmentation is possible with many allocations.",["memory","stack-heap"]),
    sa("beginner","What are C++ references and how are they different from pointers?","A reference is an alias for an existing variable. It must be initialized when declared and cannot be reseated (changed to refer to another variable). Unlike pointers: references cannot be null, no need to dereference (no * operator), no pointer arithmetic. Syntax: int& ref = x;",["references","pointers"]),
    sa("beginner","What is function overloading in C++?","Function overloading allows multiple functions with the same name but different parameter lists (number, types, or order of parameters). The compiler resolves which function to call at compile time based on the arguments. Return type alone is NOT sufficient to overload. Example: void print(int), void print(double), void print(string).",["functions","overloading"]),

    mcq("intermediate","What does RAII stand for in C++?","Runtime Allocation and Initialization Idiom","Resource Acquisition Is Initialization","Rapid Application Interface Integration","Recursive Abstraction and Inheritance Interface",1,"RAII ties resource lifetime to object lifetime. Resources are acquired in constructor, released in destructor.",["raii","memory"]),
    mcq("intermediate","What is `std::move` used for?","Copying objects","Transferring ownership (move semantics)","Moving memory blocks","Sorting containers",1,"std::move casts to rvalue reference, enabling move constructors/assignment to avoid expensive copies.",["move-semantics","rvalue"]),
    mcq("intermediate","What is the Rule of Five in C++?","Five design patterns","Destructor + copy ctor + copy= + move ctor + move=","Five access specifiers","Five template parameters",1,"If you define any of the 5 special functions, you should define all 5.",["rule-of-five","oop"]),
    mcq("intermediate","What is a `unique_ptr`?","Shared ownership smart pointer","Single-owner smart pointer","Weak reference","Raw pointer wrapper",1,"unique_ptr provides exclusive ownership with automatic cleanup; cannot be copied, only moved.",["smart-pointers","memory"]),
    mcq("intermediate","What is virtual dispatch in C++?","Compile-time function selection","Runtime function selection via vtable","Template specialization","Inline function expansion",1,"Virtual functions use vtable for runtime polymorphism.",["virtual","polymorphism"]),
    sa("intermediate","Explain the difference between `shared_ptr` and `weak_ptr` in C++.",
        "shared_ptr uses reference counting for shared ownership; the object is deleted when count reaches 0. weak_ptr is a non-owning reference to a shared_ptr-managed object; it doesn't affect the reference count. weak_ptr is used to break circular references (which would cause memory leaks with shared_ptr). To use a weak_ptr, lock() it to get a temporary shared_ptr.",["smart-pointers","memory"]),
    sa("intermediate","What are template specializations in C++?","Template specialization allows providing a custom implementation for a specific type. Full specialization: template<> class MyClass<int> {...}. Partial specialization: template<typename T> class MyClass<T*> {...} for all pointer types. Used when the generic implementation is wrong or suboptimal for a specific type.",["templates","generics"]),
    code_q("intermediate","Implement a template function for finding the maximum of two values.",
        "template <typename T>\nconst T& max_val(const T& a, const T& b) {\n    return (a > b) ? a : b;\n}\n\n// Usage:\nmax_val(3, 5);       // 5\nmax_val(3.14, 2.71); // 3.14\nmax_val(std::string(\"apple\"), std::string(\"banana\")); // banana",["templates","algorithms"]),
    code_q("intermediate","Implement a simple linked list with push_front and pop_front using C++ classes.",
        "template<typename T>\nclass LinkedList {\n    struct Node { T data; Node* next; };\n    Node* head = nullptr;\npublic:\n    void push_front(T val) {\n        head = new Node{val, head};\n    }\n    T pop_front() {\n        if (!head) throw std::underflow_error(\"empty\");\n        T val = head->data;\n        Node* tmp = head;\n        head = head->next;\n        delete tmp;\n        return val;\n    }\n    ~LinkedList() { while (head) pop_front(); }\n};",["data-structures","templates"]),
    code_q("intermediate","Write a C++ RAII file handler class.",
        "#include <fstream>\n#include <stdexcept>\n\nclass FileHandler {\n    std::fstream file;\npublic:\n    explicit FileHandler(const std::string& path, std::ios::openmode mode)\n        : file(path, mode) {\n        if (!file.is_open())\n            throw std::runtime_error(\"Cannot open: \" + path);\n    }\n    std::fstream& get() { return file; }\n    ~FileHandler() { if (file.is_open()) file.close(); }\n    // Disable copy\n    FileHandler(const FileHandler&) = delete;\n    FileHandler& operator=(const FileHandler&) = delete;\n};",["raii","files"]),

    mcq("advanced","What is CRTP (Curiously Recurring Template Pattern)?","A runtime polymorphism technique","Static polymorphism via derived class as template argument","A smart pointer pattern","A memory allocator pattern",1,"CRTP enables static (compile-time) polymorphism: template<typename D> class Base { D& self(){return static_cast<D&>(*this);} };",["templates","advanced"]),
    mcq("advanced","What is std::launder used for?","Cleaning up memory","Obtaining a valid pointer after placement new","Garbage collection","Thread safety",1,"std::launder informs the compiler that a pointer result of placement new is valid after reuse of storage.",["memory","advanced"]),
    mcq("advanced","What guarantee does `std::atomic` provide?","Unlimited performance","Lock-free guarantee","No data races on operations","Sequential consistency always",2,"std::atomic guarantees no data races; lock-free depends on the implementation.",["concurrency","atomic"]),
    sa("advanced","Explain perfect forwarding and `std::forward` in C++.",
        "Perfect forwarding passes arguments to another function while preserving their value category (lvalue/rvalue). Use forwarding references (T&&) and std::forward<T>(arg). Without std::forward, rvalues would be treated as lvalues inside the function. Example: template<typename T> void wrapper(T&& arg) { target(std::forward<T>(arg)); }. Used in emplace_back, make_unique, etc.",["templates","forwarding","rvalue"]),
    code_q("advanced","Implement a variadic template function that sums any number of arguments.",
        "// Base case\ntemplate<typename T>\nT sum(T val) { return val; }\n\n// Recursive case\ntemplate<typename T, typename... Args>\nT sum(T first, Args... rest) {\n    return first + sum(rest...);\n}\n\n// C++17 fold expression (simpler):\ntemplate<typename... Args>\nauto sum_fold(Args... args) {\n    return (... + args);\n}\n// sum(1, 2, 3, 4) == 10",["variadic-templates","fold-expressions"]),
    code_q("advanced","Implement a thread-safe queue using mutex and condition_variable.",
        "#include <queue>\n#include <mutex>\n#include <condition_variable>\n\ntemplate<typename T>\nclass ThreadSafeQueue {\n    std::queue<T> q;\n    mutable std::mutex mtx;\n    std::condition_variable cv;\npublic:\n    void push(T val) {\n        std::lock_guard<std::mutex> lock(mtx);\n        q.push(std::move(val));\n        cv.notify_one();\n    }\n    T pop() {\n        std::unique_lock<std::mutex> lock(mtx);\n        cv.wait(lock, [this]{ return !q.empty(); });\n        T val = std::move(q.front());\n        q.pop();\n        return val;\n    }\n};",["concurrency","templates"]),
    code_q("advanced","Write a C++ custom allocator for use with std::vector.",
        "template<typename T>\nstruct PoolAllocator {\n    using value_type = T;\n\n    PoolAllocator() = default;\n    template<typename U> PoolAllocator(const PoolAllocator<U>&) {}\n\n    T* allocate(std::size_t n) {\n        // In production, use a pool; here use ::operator new\n        return static_cast<T*>(::operator new(n * sizeof(T)));\n    }\n    void deallocate(T* p, std::size_t) noexcept {\n        ::operator delete(p);\n    }\n};\n\n// Usage:\nstd::vector<int, PoolAllocator<int>> v;",["allocators","templates","advanced"]),
]

# ─── HTML ─────────────────────────────────────────────────────
HTML_QUESTIONS = [
    mcq("beginner","What does HTML stand for?","Hyper Text Markup Language","High Text Modern Language","Hyper Transfer Mode Language","Hyper Text Machine Language",0,"HTML = HyperText Markup Language.",["basics"]),
    mcq("beginner","Which tag creates a hyperlink?","<link>","<href>","<a>","<url>",2,"The <a> (anchor) tag with href attribute creates hyperlinks.",["links","tags"]),
    mcq("beginner","Which tag is used for the largest heading?","<h6>","<head>","<h1>","<heading>",2,"<h1> is the largest heading; <h6> is the smallest.",["headings","semantics"]),
    mcq("beginner","What attribute specifies where an image is located?","link","path","src","href",2,"The src attribute of <img> specifies the image source URL.",["images","attributes"]),
    mcq("beginner","Which HTML element is used to define navigation links?","<nav>","<navigation>","<links>","<menu>",0,"<nav> is the semantic HTML5 element for navigation.",["semantics","html5"]),
    mcq("beginner","What does the `alt` attribute on `<img>` do?","Sets image title","Provides alternative text","Sets image size","Links the image",1,"alt text is shown when image fails to load and is read by screen readers.",["accessibility","images"]),
    mcq("beginner","Which tag creates an unordered (bulleted) list?","<ol>","<li>","<ul>","<list>",2,"<ul> creates an unordered list; items inside use <li>.",["lists","tags"]),
    sa("beginner","What is the difference between block-level and inline HTML elements?","Block-level elements (div, p, h1-h6, ul, table) start on a new line and take full available width. Inline elements (span, a, img, strong, em) flow within text and only take as much width as needed. Block elements can contain inline elements; inline elements generally cannot contain block elements.",["layout","elements"]),
    sa("beginner","Explain the purpose of the HTML <head> element.","The <head> element contains metadata about the document that is not displayed on the page: <title> (browser tab title), <meta> tags (charset, viewport, description), <link> for stylesheets, <script> tags, and <base>. It provides information for browsers and search engines.",["head","metadata"]),
    sa("beginner","What is the difference between HTML attributes and properties?","Attributes are defined in HTML markup and represent the initial values (e.g., value='hello'). Properties are JavaScript object properties that reflect the current state (element.value). After user interaction, the property changes but the attribute may remain the same. getAttribute() returns the original attribute; .value returns current state.",["dom","javascript"]),

    mcq("intermediate","Which input type shows a date picker in modern browsers?","<input type='calendar'>","<input type='date'>","<input type='datetime'>","<input type='time'>",1,"<input type='date'> shows a native date picker.",["forms","html5"]),
    mcq("intermediate","What does the `defer` attribute on a script tag do?","Loads script synchronously","Executes script after DOM is parsed","Caches the script","Prevents script loading",1,"defer loads the script in parallel and executes it after HTML parsing completes.",["scripts","performance"]),
    mcq("intermediate","Which HTML5 element represents self-contained content?","<section>","<article>","<aside>","<main>",1,"<article> is for self-contained content (blog post, news story) that makes sense independently.",["semantics","html5"]),
    mcq("intermediate","What attribute makes a form field required?","validate","mandatory","required","must",2,"The required attribute prevents form submission if the field is empty.",["forms","validation"]),
    mcq("intermediate","What is the purpose of `<meta name='viewport'>`?","SEO optimization","Controls layout on mobile browsers","Sets page encoding","Adds social media previews",1,"The viewport meta tag controls how the page is rendered on mobile devices.",["responsive","mobile"]),
    sa("intermediate","Explain the difference between <div> and <section> in HTML5.","<div> is a generic non-semantic container for grouping elements (mainly for CSS styling). <section> is semantic and represents a thematic section of content with a heading. Use <section> when the content forms a distinct part of a document (chapters, tabs), and <div> for pure styling purposes.",["semantics","html5"]),
    sa("intermediate","What are ARIA attributes and why are they important?","ARIA (Accessible Rich Internet Applications) attributes add accessibility metadata to HTML elements. role defines what an element is (e.g., role='button'), aria-label provides accessible names, aria-expanded signals state, aria-live marks regions that update dynamically. They help screen readers and assistive technologies understand dynamic web content.",["accessibility","aria"]),
    code_q("intermediate","Write an HTML form with validation for name, email, and password fields.",
        "<!DOCTYPE html>\n<html lang='en'>\n<head><meta charset='UTF-8'><title>Registration</title></head>\n<body>\n<form action='/register' method='post' novalidate>\n  <label for='name'>Name:</label>\n  <input type='text' id='name' name='name' required minlength='2' maxlength='100'>\n\n  <label for='email'>Email:</label>\n  <input type='email' id='email' name='email' required>\n\n  <label for='password'>Password:</label>\n  <input type='password' id='password' name='password'\n         required minlength='8'\n         pattern='(?=.*[A-Z])(?=.*\\d).{8,}'\n         title='Min 8 chars, 1 uppercase, 1 number'>\n\n  <button type='submit'>Register</button>\n</form>\n</body></html>",["forms","validation"]),
    sa("intermediate","What is the difference between localStorage, sessionStorage, and cookies?","localStorage: persists until cleared, ~5-10MB, per-origin, not sent to server. sessionStorage: cleared when tab closes, ~5MB, per-tab, not sent to server. Cookies: can have expiry, ~4KB, sent with every HTTP request (security concern), can be HTTPOnly and Secure. Use localStorage for persistent preferences, sessionStorage for temporary state, cookies for authentication tokens (HttpOnly).",["storage","security"]),
    code_q("intermediate","Create an accessible navigation menu with ARIA roles.",
        "<nav aria-label='Main navigation'>\n  <ul role='menubar'>\n    <li role='none'>\n      <a role='menuitem' href='/'>Home</a>\n    </li>\n    <li role='none'>\n      <button role='menuitem' aria-haspopup='true' aria-expanded='false'>\n        Products\n      </button>\n      <ul role='menu' aria-label='Products submenu' hidden>\n        <li role='none'><a role='menuitem' href='/products/a'>Product A</a></li>\n        <li role='none'><a role='menuitem' href='/products/b'>Product B</a></li>\n      </ul>\n    </li>\n  </ul>\n</nav>",["accessibility","aria"]),

    mcq("advanced","What does the `<template>` element do in HTML?","Renders hidden content","Holds client-side template content not rendered immediately","Creates repeating layouts","Defines server templates",1,"<template> holds HTML content that is not rendered but can be cloned and inserted via JavaScript.",["templates","javascript"]),
    mcq("advanced","What is Shadow DOM?","A CSS feature","A hidden DOM tree attached to an element","A server-side rendering technique","A debugging tool",1,"Shadow DOM encapsulates a sub-tree with its own scope, used in Web Components.",["web-components","shadow-dom"]),
    mcq("advanced","Which meta tag improves Core Web Vitals for LCP?","<meta name='preload'>","<link rel='preload'>","<meta http-equiv='prefetch'>","<meta name='lcp'>",1,"<link rel='preload'> preloads critical resources (fonts, hero images) to improve LCP.",["performance","web-vitals"]),
    sa("advanced","Explain Content Security Policy (CSP) and how to implement it in HTML.",
        "CSP is a security layer preventing XSS by specifying allowed sources. Implemented via HTTP header (Content-Security-Policy) or <meta http-equiv='Content-Security-Policy' content='...'> tag. Example: default-src 'self'; script-src 'self' https://trusted.com; style-src 'self' 'unsafe-inline'. Blocks inline scripts unless 'unsafe-inline' or nonces are used. Report-only mode available for testing.",["security","csp"]),
    code_q("advanced","Create a custom HTML Web Component with Shadow DOM.",
        "class UserCard extends HTMLElement {\n  constructor() {\n    super();\n    const shadow = this.attachShadow({ mode: 'open' });\n    shadow.innerHTML = `\n      <style>\n        :host { display: block; border: 1px solid #ccc; padding: 16px; }\n        h2 { color: #333; }\n      </style>\n      <h2>${this.getAttribute('name') || 'User'}</h2>\n      <p>Role: ${this.getAttribute('role') || 'Member'}</p>\n    `;\n  }\n}\ncustomElements.define('user-card', UserCard);\n// Usage: <user-card name='Alice' role='Admin'></user-card>",["web-components","shadow-dom"]),
    sa("advanced","What are Intersection Observer and Resize Observer APIs used for?","IntersectionObserver: fires callback when an element enters/exits the viewport (or another element). Used for lazy loading images, infinite scroll, analytics tracking. More performant than scroll event listeners. ResizeObserver: fires callback when an element's size changes. Used for responsive component layouts, canvas resizing. Both are asynchronous and do not block the main thread.",["performance","observers"]),
    code_q("advanced","Implement a lazy-loading image component using Intersection Observer.",
        "<!-- HTML -->\n<img class='lazy' data-src='photo.jpg' src='placeholder.jpg' alt='Photo'>\n\n<script>\nconst lazyImages = document.querySelectorAll('img.lazy');\n\nconst observer = new IntersectionObserver((entries, obs) => {\n  entries.forEach(entry => {\n    if (entry.isIntersecting) {\n      const img = entry.target;\n      img.src = img.dataset.src;\n      img.classList.remove('lazy');\n      obs.unobserve(img);\n    }\n  });\n}, { rootMargin: '200px' });\n\nlazyImages.forEach(img => observer.observe(img));\n</script>",["performance","lazy-loading"]),
    sa("advanced","What is the difference between preload, prefetch, and preconnect in HTML?","preload (<link rel='preload'>): loads a resource needed for the current page immediately (critical CSS, fonts, hero image). prefetch (<link rel='prefetch'>): loads a resource that may be needed for future navigation at low priority. preconnect (<link rel='preconnect'>): establishes early connection (DNS + TCP + TLS) to an origin, reducing latency for future requests. Use preload for current page critical resources, prefetch for next-page resources.",["performance","resource-hints"]),
    code_q("advanced","Implement an HTML dialog with accessibility and focus trap.",
        "<!-- HTML -->\n<button id='open-btn'>Open Dialog</button>\n<dialog id='myDialog' aria-labelledby='dialog-title' aria-modal='true'>\n  <h2 id='dialog-title'>Confirm Action</h2>\n  <p>Are you sure?</p>\n  <button id='confirm-btn'>Confirm</button>\n  <button id='cancel-btn'>Cancel</button>\n</dialog>\n\n<script>\nconst dialog = document.getElementById('myDialog');\ndocument.getElementById('open-btn').addEventListener('click', () => {\n  dialog.showModal();\n  document.getElementById('confirm-btn').focus();\n});\ndocument.getElementById('cancel-btn').addEventListener('click', () => dialog.close());\ndialog.addEventListener('cancel', e => e.preventDefault());\n</script>",["accessibility","dialog"]),
]

# ─── CSS ──────────────────────────────────────────────────────
CSS_QUESTIONS = [
    mcq("beginner","Which property changes text color in CSS?","font-color","text-color","color","foreground",2,"The 'color' property sets the foreground color of text.",["color","basics"]),
    mcq("beginner","What does CSS stand for?","Computer Style Sheets","Cascading Style Sheets","Creative Style Syntax","Colorful Styling System",1,"CSS = Cascading Style Sheets.",["basics"]),
    mcq("beginner","Which selector targets elements with class 'box'?","#box",".box","box","*box",1,".box is the class selector syntax.",["selectors"]),
    mcq("beginner","What value of `display` makes an element a flex container?","block","inline","flex","grid",2,"display: flex enables flexbox layout.",["flexbox","display"]),
    mcq("beginner","Which CSS property controls the space INSIDE an element's border?","margin","border","padding","spacing",2,"Padding is inside the border; margin is outside.",["box-model"]),
    mcq("beginner","How do you select all `<p>` elements inside a `<div>`?","div + p","div > p","div p","div.p",2,"div p selects all p descendants of div (any depth).",["selectors","combinators"]),
    mcq("beginner","What does `position: absolute` do?","Positions relative to the viewport","Positions relative to the nearest positioned ancestor","Makes element fixed","Removes from document flow and positions at (0,0)",1,"absolute positioning removes from normal flow and positions relative to the nearest positioned ancestor.",["positioning"]),
    sa("beginner","Explain the CSS Box Model.","The CSS Box Model describes how elements are rendered as boxes with: Content (text/images), Padding (space between content and border), Border (surrounds padding), and Margin (space outside border). Total element width = content + padding + border + margin. box-sizing: border-box includes padding and border in the width calculation.",["box-model","layout"]),
    sa("beginner","What is the difference between margin and padding in CSS?","Margin is the space outside the border, between elements. It can be negative and collapses vertically between sibling elements. Padding is the space inside the border, between content and border. It cannot be negative and does not collapse. Backgrounds apply to padding but not margin.",["box-model","spacing"]),
    sa("beginner","What is CSS specificity and how is it calculated?","Specificity determines which CSS rule applies when multiple rules target the same element. Calculated as (a, b, c) where: a = inline styles (highest), b = ID selectors count, c = class/attribute/pseudo-class count, d = element/pseudo-element count. #id.class p = (0,1,1,1). Equal specificity: last rule wins.",["specificity","cascade"]),

    mcq("intermediate","Which Flexbox property controls the direction of items?","flex-wrap","justify-content","flex-direction","align-items",2,"flex-direction sets row, row-reverse, column, or column-reverse.",["flexbox","layout"]),
    mcq("intermediate","What does `z-index` control?","Element size","Stacking order of positioned elements","Element transparency","Animation delay",1,"z-index controls which positioned element appears on top.",["positioning","z-index"]),
    mcq("intermediate","Which CSS unit is relative to the root element's font-size?","em","rem","vh","px",1,"rem (root em) is relative to the <html> element's font-size.",["units","typography"]),
    mcq("intermediate","What CSS Grid property defines column sizes?","grid-rows","grid-template-columns","column-size","grid-columns",1,"grid-template-columns defines the number and width of columns.",["grid","layout"]),
    mcq("intermediate","Which pseudo-class targets the first child of its parent?",":first-of-type",":first-child",":nth-child(1)","Both B and C",3,"Both :first-child and :nth-child(1) target the first child.",["pseudo-classes","selectors"]),
    sa("intermediate","Explain CSS Custom Properties (CSS Variables) and their benefits.",
        "CSS Custom Properties (--variable-name) store reusable values in CSS. Declared with -- prefix in a selector (usually :root): :root { --primary: #3776AB; }. Used with var(): color: var(--primary, fallback). Benefits: dynamic (can change with JS), inherit through DOM, enable theming, reduce repetition, work in media queries. Unlike preprocessor variables, they are live.",["variables","css-modern"]),
    sa("intermediate","What is the difference between `display: none` and `visibility: hidden`?","display: none removes the element from document flow entirely (takes no space). visibility: hidden hides the element but it still occupies space in the layout. opacity: 0 is similar to visibility: hidden but also hides from assistive technologies. For accessibility, prefer aria-hidden='true' over CSS hiding.",["visibility","display"]),
    code_q("intermediate","Write CSS to create a responsive 3-column card layout using CSS Grid.",
        ".card-grid {\n  display: grid;\n  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));\n  gap: 24px;\n  padding: 24px;\n}\n\n.card {\n  background: white;\n  border-radius: 12px;\n  padding: 24px;\n  box-shadow: 0 2px 8px rgba(0,0,0,0.1);\n  transition: transform 0.2s, box-shadow 0.2s;\n}\n\n.card:hover {\n  transform: translateY(-4px);\n  box-shadow: 0 8px 24px rgba(0,0,0,0.15);\n}\n\n@media (max-width: 600px) {\n  .card-grid { grid-template-columns: 1fr; padding: 12px; }\n}",["grid","responsive"]),
    code_q("intermediate","Create a CSS animated loading spinner.",
        "@keyframes spin {\n  from { transform: rotate(0deg); }\n  to { transform: rotate(360deg); }\n}\n\n.spinner {\n  width: 40px;\n  height: 40px;\n  border: 4px solid rgba(0,0,0,0.1);\n  border-top-color: #3776AB;\n  border-radius: 50%;\n  animation: spin 0.8s linear infinite;\n}\n\n/* Usage: <div class='spinner'></div> */",["animations","keyframes"]),
    sa("intermediate","Explain the difference between CSS Flexbox and CSS Grid and when to use each.",
        "Flexbox: 1-dimensional layout (row OR column). Best for: navigation bars, centering, distributing items along one axis, component-level layouts. Grid: 2-dimensional layout (rows AND columns simultaneously). Best for: page-level layouts, complex grids, aligning items in both axes. Rule of thumb: Flexbox for components, Grid for page layouts. They can be combined: grid container with flex item children.",["flexbox","grid","layout"]),

    mcq("advanced","What is CSS containment (`contain` property) used for?","Variable scoping","Isolating element subtrees for performance","Creating new stacking context","Preventing inheritance",1,"contain: layout paint style allows the browser to optimize rendering by isolating subtrees.",["performance","rendering"]),
    mcq("advanced","What is a CSS Houdini API?","A CSS hack library","Low-level browser rendering APIs exposed to JavaScript","A CSS preprocessor","A polyfill system",1,"CSS Houdini exposes CSS engine internals (Paint, Layout, Animation Worklets) allowing JS to extend CSS.",["houdini","advanced"]),
    mcq("advanced","Which CSS property enables hardware-accelerated animation?","animation-hardware","transform and opacity","will-change: all","gpu: enable",1,"Animating transform and opacity triggers GPU compositing, avoiding layout/paint.",["performance","animation"]),
    sa("advanced","Explain the Critical Rendering Path and how CSS affects it.",
        "The CRP is the sequence of steps to convert HTML+CSS+JS into pixels: DOM construction → CSSOM construction → Render tree → Layout → Paint → Composite. CSS is render-blocking: the browser must build the CSSOM before painting. Optimizations: minimize CSS file size, inline critical CSS, use media queries to defer non-critical CSS (media='print'), remove unused CSS, avoid complex selectors.",["performance","rendering"]),
    code_q("advanced","Implement CSS for a glassmorphism card effect.",
        ".glass-card {\n  background: rgba(255, 255, 255, 0.15);\n  backdrop-filter: blur(10px);\n  -webkit-backdrop-filter: blur(10px);\n  border: 1px solid rgba(255, 255, 255, 0.2);\n  border-radius: 16px;\n  padding: 32px;\n  box-shadow:\n    0 8px 32px rgba(0, 0, 0, 0.3),\n    inset 0 1px 0 rgba(255, 255, 255, 0.3);\n  color: white;\n}\n\n/* Parent needs a background image/gradient for the effect to show */\n.glass-container {\n  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);\n  min-height: 100vh;\n  display: grid;\n  place-items: center;\n}",["glassmorphism","visual-effects"]),
    code_q("advanced","Write CSS for a smooth theme toggle (dark/light mode) using CSS variables.",
        ":root {\n  --bg: #ffffff;\n  --text: #1a1a1a;\n  --accent: #3776AB;\n  --card-bg: #f5f5f5;\n  color-scheme: light;\n}\n\n[data-theme='dark'] {\n  --bg: #0d1117;\n  --text: #e6edf3;\n  --accent: #58a6ff;\n  --card-bg: #161b22;\n  color-scheme: dark;\n}\n\nbody {\n  background: var(--bg);\n  color: var(--text);\n  transition: background 0.3s ease, color 0.3s ease;\n}\n\n/* Toggle via JS: document.documentElement.dataset.theme = 'dark' */",["theming","variables","dark-mode"]),
    sa("advanced","What are CSS Layers (@layer) and how do they improve specificity management?","@layer allows organizing CSS into named layers with explicit cascade order: @layer reset, base, components, utilities. Styles in later layers win over earlier ones regardless of specificity. This solves specificity wars. Example: @layer utilities { .text-red { color: red; } } — utility styles win over components even with low specificity. Unlayered styles are treated as highest priority.",["cascade","layers","css-modern"]),
    code_q("advanced","Implement a CSS scroll-driven animation (2023 feature).",
        "/* Scroll-driven fade-in animation */\n@keyframes fade-up {\n  from { opacity: 0; transform: translateY(40px); }\n  to { opacity: 1; transform: translateY(0); }\n}\n\n.animate-on-scroll {\n  animation: fade-up linear both;\n  animation-timeline: view();\n  animation-range: entry 0% entry 40%;\n}\n\n/* Scroll progress indicator */\n@keyframes progress {\n  from { transform: scaleX(0); }\n  to { transform: scaleX(1); }\n}\n\n.scroll-progress {\n  position: fixed;\n  top: 0; left: 0;\n  width: 100%; height: 4px;\n  background: #3776AB;\n  transform-origin: left;\n  animation: progress linear;\n  animation-timeline: scroll();\n}",["scroll-animations","css-modern"]),
]

# ─── POWER BI ─────────────────────────────────────────────────
POWERBI_QUESTIONS = [
    mcq("beginner","What does DAX stand for in Power BI?","Data Analysis Expressions","Data Application Extension","Direct Analysis Exchange","Database Aggregation Expression",0,"DAX (Data Analysis Expressions) is the formula language used in Power BI.",["dax","basics"]),
    mcq("beginner","Which view in Power BI Desktop is used to create reports?","Data view","Model view","Report view","Query view",2,"Report view is where you add visuals and create report pages.",["power-bi","ui"]),
    mcq("beginner","What is a slicer in Power BI?","A filter visual","A DAX function","A data source","A calculated column",0,"A slicer is a visual that filters other visuals on the report page.",["visuals","filtering"]),
    mcq("beginner","Which Power BI service allows sharing reports with colleagues?","Power BI Desktop","Power BI Report Server","Power BI Service","Power BI Gateway",2,"Power BI Service (app.powerbi.com) enables sharing and collaboration.",["service","sharing"]),
    mcq("beginner","What file extension do Power BI Desktop files use?",".pbix",".pbi",".xlsx",".pbis",0,"Power BI Desktop files use the .pbix extension.",["files","basics"]),
    mcq("beginner","What is Power Query used for in Power BI?","Creating visuals","Writing DAX","Data transformation and loading","Publishing reports",2,"Power Query (M language) is the ETL tool for cleaning and shaping data.",["power-query","etl"]),
    mcq("beginner","Which function calculates the total for a column in DAX?","COUNT()","SUM()","TOTAL()","ADD()",1,"SUM(ColumnName) sums all values in a column.",["dax","aggregation"]),
    sa("beginner","What is the difference between a measure and a calculated column in Power BI?","A calculated column is evaluated row-by-row and stored in the table (increases model size). A measure is evaluated dynamically at query time based on filter context (not stored). Use calculated columns for row-level calculations referenced as filters/rows. Use measures for aggregations displayed in visuals.",["dax","data-model"]),
    sa("beginner","Explain what a Star Schema is and why it's recommended for Power BI.","A Star Schema has one central fact table (transactional data) surrounded by dimension tables (descriptive attributes). The fact table contains measures and foreign keys; dimension tables have attributes. Benefits for Power BI: faster query performance, simpler DAX, better compression, easier relationships. Avoid snowflake schemas (normalized dimensions) as they complicate DAX.",["data-modeling","star-schema"]),
    sa("beginner","What is the difference between DirectQuery and Import mode in Power BI?","Import mode: data is loaded into Power BI's in-memory columnar store (VertiPaq). Fast queries, up to 1GB in service, manual refresh needed. DirectQuery: queries are sent to the source in real-time, no data stored in Power BI. Good for large datasets or real-time needs, but slower and limited DAX. Composite mode: mix of both.",["connectivity","performance"]),

    mcq("intermediate","What does `CALCULATE()` do in DAX?","Performs a calculation","Evaluates an expression in a modified filter context","Creates a new table","Filters rows",1,"CALCULATE changes the filter context in which a measure or expression is evaluated.",["dax","filter-context"]),
    mcq("intermediate","What is the difference between RELATED() and RELATEDTABLE() in DAX?","No difference","RELATED gets a value from many side; RELATEDTABLE returns a table from one side","RELATED returns table; RELATEDTABLE returns value","RELATED is for measures; RELATEDTABLE for columns",1,"RELATED: navigate to many-to-one side (get single value). RELATEDTABLE: navigate to one-to-many side (get related table).",["dax","relationships"]),
    mcq("intermediate","Which function returns running total correctly in DAX?","CUMULATE()","CALCULATE with DATESBETWEEN","TOTALYTD()","RUNNING_TOTAL()",2,"TOTALYTD(measure, date_column) computes year-to-date running total.",["dax","time-intelligence"]),
    mcq("intermediate","What is Row Context in DAX?","The current filter applied by slicers","The current row being iterated in a table","The active relationships","The visual's data",1,"Row context is the current row in iteration functions like SUMX, FILTER, and calculated columns.",["dax","context"]),
    sa("intermediate","Explain the difference between SUMX and SUM in DAX.",
        "SUM(table[column]) aggregates all values in a column within the current filter context. SUMX(table, expression) is an iterator that evaluates an expression row by row and sums the results. Use SUMX when you need row-level calculation first: SUMX(Sales, Sales[Qty] * Sales[Price]) vs SUM(Sales[Revenue]) if revenue is pre-calculated.",["dax","iterators"]),
    sa("intermediate","What is filter propagation and cross-filter direction in Power BI?",
        "Filter propagation: filters from one table flow through relationships to related tables. Cross-filter direction: Single = filters flow from one side to many side (default, recommended). Both = filters flow both ways (can cause ambiguity, performance issues). Use Both only when necessary (many-to-many or bi-directional filtering). Active vs inactive relationships: only one active per table pair.",["data-model","relationships"]),
    code_q("intermediate","Write a DAX measure for Year-over-Year growth percentage.",
        "YoY Growth % = \nVAR CurrentYearSales = [Total Sales]\nVAR PriorYearSales = CALCULATE([Total Sales], SAMEPERIODLASTYEAR('Date'[Date]))\nRETURN\n    IF(\n        ISBLANK(PriorYearSales) || PriorYearSales = 0,\n        BLANK(),\n        DIVIDE(CurrentYearSales - PriorYearSales, PriorYearSales)\n    )",["dax","time-intelligence"]),
    code_q("intermediate","Write a DAX measure to calculate a 3-month moving average.",
        "3M Moving Avg = \nVAR LastDate = MAX('Date'[Date])\nVAR PeriodStart = EDATE(LastDate, -2) -- 3 months back\nVAR SalesInPeriod = \n    CALCULATE(\n        [Total Sales],\n        DATESBETWEEN('Date'[Date], DATE(YEAR(PeriodStart), MONTH(PeriodStart), 1), LastDate)\n    )\nVAR MonthCount = \n    CALCULATE(\n        DISTINCTCOUNT('Date'[Month]),\n        DATESBETWEEN('Date'[Date], DATE(YEAR(PeriodStart), MONTH(PeriodStart), 1), LastDate)\n    )\nRETURN DIVIDE(SalesInPeriod, MonthCount)",["dax","time-intelligence","moving-average"]),
    sa("intermediate","What are bookmarks in Power BI and how are they used?","Bookmarks capture the current state of a report page (filters, selections, visibility, scroll position). Uses: alternate views (show/hide panels), storytelling (guided navigation), toggle buttons, custom navigation. Bookmarks can be scoped to specific visuals. Add via View > Bookmarks panel. Use 'Update' to refresh. Combined with Selection pane for layer control.",["bookmarks","ux"]),
    code_q("intermediate","Write a DAX measure that ranks customers by sales within each region.",
        "Customer Rank by Region = \nRANKX(\n    FILTER(\n        ALLSELECTED('Customer'),\n        'Customer'[Region] = MAX('Customer'[Region])\n    ),\n    [Total Sales],\n    ,\n    DESC,\n    DENSE\n)",["dax","ranking"]),

    mcq("advanced","What is VertiPaq and why is it important for Power BI performance?","A DAX function","Power BI's in-memory columnar database engine","A data connector","A Power Query step",1,"VertiPaq is Power BI's columnar storage engine that compresses data for fast in-memory analytics.",["performance","internals"]),
    mcq("advanced","What does USERELATIONSHIP() do in DAX?","Creates a new relationship","Activates an inactive relationship in a calculation","Removes a relationship","Changes join type",1,"USERELATIONSHIP activates an inactive relationship within CALCULATE scope.",["dax","relationships"]),
    sa("advanced","Explain context transition in DAX and when it occurs.",
        "Context transition converts row context to equivalent filter context when a measure is referenced inside an iterator (SUMX, FILTER, CALCULATE). Each row's values become filters on the data model. This can be expensive. Example: SUMX(Sales, [Measure]) triggers context transition for every row. To avoid, replace measure reference with the measure's expression or use CALCULATE explicitly. Understand this to debug unexpected measure behavior.",["dax","advanced","context"]),
    sa("advanced","What are Aggregations in Power BI and when should you use them?",
        "Aggregations allow mixed modes: pre-aggregated tables in Import mode serve queries while detail tables use DirectQuery. When a query matches an aggregation, VertiPaq answers it (fast). Otherwise, DirectQuery handles it. Use for large datasets where full import is impossible but common queries can be pre-aggregated. Set up via Manage Aggregations in Model view. Requires a RLS-compatible model.",["performance","aggregations","advanced"]),
    code_q("advanced","Write a DAX measure using SWITCH with dynamic formatting for a KPI.",
        "KPI Status = \nVAR ActualSales = [Total Sales]\nVAR TargetSales = [Sales Target]\nVAR Ratio = DIVIDE(ActualSales, TargetSales)\nRETURN\n    SWITCH(\n        TRUE(),\n        Ratio >= 1.1, \"🟢 Exceeds Target (\" & FORMAT(Ratio, \"0%\") & \")\",\n        Ratio >= 0.9, \"🟡 On Track (\" & FORMAT(Ratio, \"0%\") & \")\",\n        Ratio >= 0.7, \"🟠 At Risk (\" & FORMAT(Ratio, \"0%\") & \")\",\n        \"🔴 Critical (\" & FORMAT(Ratio, \"0%\") & \")\"\n    )",["dax","kpi","switch"]),
    code_q("advanced","Write a DAX expression to implement RLS (Row Level Security) for regional managers.",
        "-- In Power BI Model > Manage Roles, create 'RegionalManager' role\n-- Table filter expression on Sales table:\n[Region] = LOOKUPVALUE(\n    Employees[Region],\n    Employees[Email],\n    USERPRINCIPALNAME()\n)\n\n-- This filters Sales to show only rows where Region matches\n-- the logged-in user's region from the Employees table.\n-- Test with 'View as > Regional Manager' in Desktop.",["rls","security","dax"]),
    sa("advanced","What is the difference between ALLSELECTED, ALL, and ALLEXCEPT in DAX?","ALL(table/column): removes all filters from table or column, regardless of user selections. ALLEXCEPT(table, col1, col2): removes all filters EXCEPT specified columns. ALLSELECTED(table/column): removes filter context from current visual/calculation but respects outer query filters (slicers/page filters). Use ALLSELECTED for percent-of-selected-total calculations. Use ALL for absolute calculations ignoring all filters.",["dax","filter-manipulation","advanced"]),
    code_q("advanced","Write M (Power Query) code to unpivot a matrix of monthly sales into rows.",
        "let\n    Source = Excel.CurrentWorkbook(){[Name=\"SalesMatrix\"]}[Content],\n    #\"Changed Type\" = Table.TransformColumnTypes(Source,{\n        {\"Product\", type text}\n    }),\n    #\"Unpivoted Columns\" = Table.UnpivotOtherColumns(\n        #\"Changed Type\",\n        {\"Product\"},\n        \"Month\",\n        \"Sales\"\n    ),\n    #\"Parsed Month\" = Table.TransformColumnTypes(#\"Unpivoted Columns\",{\n        {\"Sales\", type number},\n        {\"Month\", type date}\n    })\nin\n    #\"Parsed Month\"",["power-query","m-language","etl"]),
]


TECH_QUESTIONS_MAP = {
    "python": PYTHON_QUESTIONS,
    "java": JAVA_QUESTIONS,
    "c": C_QUESTIONS,
    "cpp": CPP_QUESTIONS,
    "html": HTML_QUESTIONS,
    "css": CSS_QUESTIONS,
    "powerbi": POWERBI_QUESTIONS,
}


async def seed_questions():
    print("Initialize database and base technologies...")
    await create_tables()
    await _seed_initial_data()
    
    async with AsyncSessionLocal() as db:
        # Load technologies
        result = await db.execute(select(Technology).where(Technology.is_active == True))
        technologies = {t.slug: t for t in result.scalars().all()}

        if not technologies:
            print("❌ No technologies found. Run the app first to seed technologies.")
            return

        total_added = 0
        for slug, tech in technologies.items():
            questions_data = TECH_QUESTIONS_MAP.get(slug, [])
            if not questions_data:
                print(f"⚠️  No questions defined for: {tech.name} ({slug})")
                continue

            # Check existing
            existing = await db.execute(
                select(Question).where(Question.technology_id == tech.id)
            )
            existing_count = len(existing.scalars().all())
            if existing_count >= len(questions_data):
                print(f"✅ {tech.name}: {existing_count} questions already seeded, skipping.")
                continue

            from app.services.assessment_service import generate_access_code
            added = 0
            for qdata in questions_data:
                q = Question(
                    id=str(uuid.uuid4()),
                    technology_id=tech.id,
                    question_type=qdata["question_type"],
                    difficulty=qdata["difficulty"],
                    question_text=qdata["question_text"],
                    options=qdata.get("options"),
                    correct_answer=qdata.get("correct_answer"),
                    explanation=qdata.get("explanation", ""),
                    max_score=qdata.get("max_score", 10),
                    tags=qdata.get("tags", []),
                    source=qdata.get("source", "manual"),
                    is_active=True,
                )
                db.add(q)
                added += 1

            # Seed a default assessment config for this technology
            existing_config = await db.execute(
                select(AssessmentConfig).where(AssessmentConfig.technology_id == tech.id)
            )
            if not existing_config.scalar_one_or_none():
                # Get the first user as admin
                from app.models.user import User
                admin = await db.execute(select(User).limit(1))
                admin_user = admin.scalar_one_or_none()
                admin_id = admin_user.id if admin_user else None

                q_result = await db.execute(
                    select(Question.id).where(Question.technology_id == tech.id).limit(15)
                )
                selected = [row[0] for row in q_result.fetchall()]

                config = AssessmentConfig(
                    id=str(uuid.uuid4()),
                    access_code=generate_access_code(),
                    title=f"{tech.name} Default Assessment",
                    technology_id=tech.id,
                    difficulty_mix={"beginner": 5, "intermediate": 5, "advanced": 5},
                    total_questions=len(selected) if selected else 15,
                    duration_minutes=60,
                    passing_score=60,
                    instructions="Default auto-generated assessment.",
                    question_ids=selected,
                    created_by=admin_id,
                )
                db.add(config)
            
            await db.commit()
            print(f"✅ {tech.name}: {added} questions seeded.")
            total_added += added

        print(f"\n🎉 Total questions seeded: {total_added}")


if __name__ == "__main__":
    asyncio.run(seed_questions())

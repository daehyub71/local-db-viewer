"""
SQL syntax highlighter for QPlainTextEdit.
"""

import re
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PySide6.QtCore import Qt


class SQLSyntaxHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for SQL with VS Code Dark+ theme colors.
    """

    # SQL keywords
    KEYWORDS = [
        'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'IN', 'IS', 'NULL',
        'AS', 'ON', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'CROSS', 'FULL',
        'ORDER', 'BY', 'ASC', 'DESC', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET',
        'UNION', 'ALL', 'DISTINCT', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
        'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE', 'TRUNCATE',
        'CREATE', 'ALTER', 'DROP', 'TABLE', 'INDEX', 'VIEW', 'DATABASE',
        'PRIMARY', 'KEY', 'FOREIGN', 'REFERENCES', 'CONSTRAINT', 'UNIQUE',
        'DEFAULT', 'CHECK', 'CASCADE', 'RESTRICT', 'IF', 'EXISTS', 'REPLACE',
        'BETWEEN', 'LIKE', 'GLOB', 'ESCAPE', 'COLLATE', 'NOCASE',
        'BEGIN', 'COMMIT', 'ROLLBACK', 'TRANSACTION', 'SAVEPOINT',
        'EXPLAIN', 'QUERY', 'PLAN', 'ANALYZE', 'VACUUM', 'REINDEX',
        'PRAGMA', 'ATTACH', 'DETACH', 'WITH', 'RECURSIVE', 'EXCEPT', 'INTERSECT',
        'NATURAL', 'USING', 'INDEXED', 'CAST', 'COALESCE', 'NULLIF', 'IFNULL',
        'TRUE', 'FALSE',
    ]

    # SQL functions
    FUNCTIONS = [
        'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'TOTAL', 'GROUP_CONCAT',
        'ABS', 'ROUND', 'RANDOM', 'LENGTH', 'LOWER', 'UPPER', 'TRIM',
        'LTRIM', 'RTRIM', 'SUBSTR', 'REPLACE', 'INSTR', 'PRINTF',
        'TYPEOF', 'UNICODE', 'ZEROBLOB', 'HEX', 'QUOTE', 'CHAR',
        'DATE', 'TIME', 'DATETIME', 'JULIANDAY', 'STRFTIME',
        'CHANGES', 'LAST_INSERT_ROWID', 'TOTAL_CHANGES',
        'SQLITE_VERSION', 'SQLITE_SOURCE_ID',
        'IIF', 'LIKELIHOOD', 'LIKELY', 'UNLIKELY',
    ]

    # Data types
    DATA_TYPES = [
        'INTEGER', 'INT', 'SMALLINT', 'BIGINT', 'TINYINT',
        'REAL', 'DOUBLE', 'FLOAT', 'DECIMAL', 'NUMERIC',
        'TEXT', 'VARCHAR', 'CHAR', 'CLOB', 'STRING',
        'BLOB', 'BINARY', 'VARBINARY',
        'BOOLEAN', 'BOOL',
        'DATE', 'DATETIME', 'TIMESTAMP',
    ]

    def __init__(self, document):
        super().__init__(document)
        self._init_formats()
        self._init_rules()

    def _init_formats(self):
        """Initialize text formats for different token types."""
        # Keywords - Blue
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#569CD6"))
        self.keyword_format.setFontWeight(QFont.Bold)

        # Functions - Yellow
        self.function_format = QTextCharFormat()
        self.function_format.setForeground(QColor("#DCDCAA"))

        # Data types - Cyan
        self.type_format = QTextCharFormat()
        self.type_format.setForeground(QColor("#4EC9B0"))

        # Strings - Orange
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#CE9178"))

        # Numbers - Light green
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor("#B5CEA8"))

        # Comments - Green
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#6A9955"))
        self.comment_format.setFontItalic(True)

        # Operators - Light gray
        self.operator_format = QTextCharFormat()
        self.operator_format.setForeground(QColor("#D4D4D4"))

        # Identifiers (quoted) - Light blue
        self.identifier_format = QTextCharFormat()
        self.identifier_format.setForeground(QColor("#9CDCFE"))

    def _init_rules(self):
        """Initialize highlighting rules."""
        self.rules = []

        # Keywords
        keyword_pattern = r'\b(' + '|'.join(self.KEYWORDS) + r')\b'
        self.rules.append((re.compile(keyword_pattern, re.IGNORECASE), self.keyword_format))

        # Functions
        function_pattern = r'\b(' + '|'.join(self.FUNCTIONS) + r')\s*\('
        self.rules.append((re.compile(function_pattern, re.IGNORECASE), self.function_format))

        # Data types
        type_pattern = r'\b(' + '|'.join(self.DATA_TYPES) + r')\b'
        self.rules.append((re.compile(type_pattern, re.IGNORECASE), self.type_format))

        # Numbers (integers and floats)
        self.rules.append((re.compile(r'\b\d+\.?\d*\b'), self.number_format))

        # Single-quoted strings
        self.rules.append((re.compile(r"'[^']*'"), self.string_format))

        # Double-quoted identifiers
        self.rules.append((re.compile(r'"[^"]*"'), self.identifier_format))

        # Backtick identifiers (MySQL style, also works in SQLite)
        self.rules.append((re.compile(r'`[^`]*`'), self.identifier_format))

        # Square bracket identifiers (SQL Server style)
        self.rules.append((re.compile(r'\[[^\]]*\]'), self.identifier_format))

        # Single-line comments: -- comment
        self.rules.append((re.compile(r'--[^\n]*'), self.comment_format))

        # Operators
        self.rules.append((re.compile(r'[+\-*/%=<>!&|~^]'), self.operator_format))

    def highlightBlock(self, text):
        """Apply syntax highlighting to a block of text."""
        # Apply each rule
        for pattern, format in self.rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format)

        # Handle multi-line comments: /* ... */
        self._highlight_multiline_comments(text)

    def _highlight_multiline_comments(self, text):
        """Handle multi-line comment highlighting."""
        start_pattern = re.compile(r'/\*')
        end_pattern = re.compile(r'\*/')

        self.setCurrentBlockState(0)

        start_index = 0
        if self.previousBlockState() != 1:
            match = start_pattern.search(text)
            start_index = match.start() if match else -1

        while start_index >= 0:
            end_match = end_pattern.search(text, start_index)

            if end_match is None:
                # Comment continues to next block
                self.setCurrentBlockState(1)
                comment_length = len(text) - start_index
            else:
                # Comment ends in this block
                comment_length = end_match.end() - start_index

            self.setFormat(start_index, comment_length, self.comment_format)

            # Look for next comment start
            match = start_pattern.search(text, start_index + comment_length)
            start_index = match.start() if match else -1

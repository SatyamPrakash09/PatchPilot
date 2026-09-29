from dataclasses import dataclass


@dataclass
class Symbol:
    name: str
    kind: str
    start_line: int
    end_line: int
    start_byte: int
    end_byte: int


DEFINITION_TYPES = {
    "function_definition": "function",
    "async_function_definition": "async_function",
    "class_definition": "class",
}


def extract_symbols(node, source: bytes) -> list[Symbol]:
    symbols = []

    if node.type in DEFINITION_TYPES:
        name_node = node.child_by_field_name("name")

        if name_node:
            name = source[
                name_node.start_byte:name_node.end_byte
            ].decode("utf-8")

            symbols.append(
                Symbol(
                    name=name,
                    kind=DEFINITION_TYPES[node.type],
                    start_line=node.start_point.row + 1,
                    end_line=node.end_point.row + 1,
                    start_byte=node.start_byte,
                    end_byte=node.end_byte,
                )
            )

    elif node.type == "decorated_definition":
        definition_node = None

        for child in node.children:
            if child.type in DEFINITION_TYPES:
                definition_node = child
                break

        if definition_node:
            name_node = definition_node.child_by_field_name("name")

            if name_node:
                name = source[
                    name_node.start_byte:name_node.end_byte
                ].decode("utf-8")

                symbols.append(
                    Symbol(
                        name=name,
                        kind=DEFINITION_TYPES[definition_node.type],
                        start_line=node.start_point.row + 1,
                        end_line=node.end_point.row + 1,
                        start_byte=node.start_byte,
                        end_byte=node.end_byte,
                    )
                )

    for child in node.children:
        symbols.extend(
            extract_symbols(child, source)
        )

    return symbols

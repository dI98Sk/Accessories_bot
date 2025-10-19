"""
Процессор Excel файлов с сохранением изображений.
Работает напрямую с XML внутри xlsx файла.
"""
import os
import shutil
import zipfile
import tempfile
import xml.etree.ElementTree as ET
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class XlsxImagePreservingProcessor:
    """
    Обрабатывает xlsx файлы с сохранением изображений.
    xlsx файл это ZIP архив с XML файлами.
    Мы модифицируем только XML с данными ячеек, не трогая изображения.
    """
    
    # Пространства имен XML в xlsx файлах
    NAMESPACES = {
        'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    }
    
    @staticmethod
    def update_prices_in_xlsx(
        input_file: str,
        output_file: str,
        markup: float,
        price_column: int = 4,
        header_row: int = 5
    ) -> int:
        """
        Обновляет цены в xlsx файле, сохраняя все изображения и форматирование.
        
        Args:
            input_file: Путь к входному файлу
            output_file: Путь к выходному файлу
            markup: Наценка для добавления к ценам
            price_column: Номер колонки с ценой (1-индексация, A=1, B=2, C=3, D=4...)
            header_row: Номер строки заголовка
        
        Returns:
            Количество обновленных цен
        """
        try:
            # Создаем временную директорию
            with tempfile.TemporaryDirectory() as temp_dir:
                # Копируем исходный файл
                shutil.copy2(input_file, output_file)
                
                # Распаковываем xlsx (это zip архив)
                extract_dir = os.path.join(temp_dir, 'xlsx_content')
                with zipfile.ZipFile(output_file, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                # Обрабатываем каждый лист
                worksheets_dir = os.path.join(extract_dir, 'xl', 'worksheets')
                if not os.path.exists(worksheets_dir):
                    logger.warning("Не найдена директория с листами")
                    return 0
                
                total_updated = 0
                
                # Обрабатываем все листы
                for sheet_file in os.listdir(worksheets_dir):
                    if sheet_file.endswith('.xml'):
                        sheet_path = os.path.join(worksheets_dir, sheet_file)
                        updated = XlsxImagePreservingProcessor._update_sheet_prices(
                            sheet_path, markup, price_column, header_row
                        )
                        total_updated += updated
                        logger.debug(f"Обработан лист {sheet_file}: {updated} цен")
                
                # Упаковываем обратно в xlsx
                with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                    for root, dirs, files in os.walk(extract_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, extract_dir)
                            zip_ref.write(file_path, arcname)
                
                logger.info(f"Обновлено цен: {total_updated}")
                return total_updated
                
        except Exception as e:
            logger.error(f"Ошибка при обработке xlsx файла: {e}", exc_info=True)
            # В случае ошибки просто копируем исходный файл
            shutil.copy2(input_file, output_file)
            return 0
    
    @staticmethod
    def _update_sheet_prices(
        sheet_path: str,
        markup: float,
        price_column: int,
        header_row: int
    ) -> int:
        """
        Обновляет цены в конкретном листе (XML файле).
        
        Args:
            sheet_path: Путь к XML файлу листа
            markup: Наценка
            price_column: Колонка с ценой
            header_row: Строка заголовка
        
        Returns:
            Количество обновленных ячеек
        """
        try:
            # Парсим XML
            ET.register_namespace('', XlsxImagePreservingProcessor.NAMESPACES['main'])
            tree = ET.parse(sheet_path)
            root = tree.getroot()
            
            # Находим все ячейки
            updated_count = 0
            column_letter = XlsxImagePreservingProcessor._column_number_to_letter(price_column)
            
            # Находим элемент sheetData
            ns = XlsxImagePreservingProcessor.NAMESPACES['main']
            sheet_data = root.find(f'.//{{{ns}}}sheetData')
            
            if sheet_data is None:
                return 0
            
            # Обрабатываем строки
            for row in sheet_data.findall(f'{{{ns}}}row'):
                row_num = int(row.get('r', 0))
                
                # Пропускаем строки до header_row
                if row_num <= header_row:
                    continue
                
                # Ищем ячейку в нужной колонке
                cell_ref = f'{column_letter}{row_num}'
                for cell in row.findall(f'{{{ns}}}c'):
                    if cell.get('r') == cell_ref:
                        # Проверяем что это число
                        cell_type = cell.get('t')
                        if cell_type not in [None, 'n']:  # n = number, None тоже число
                            continue
                        
                        # Находим значение
                        value_elem = cell.find(f'{{{ns}}}v')
                        if value_elem is not None and value_elem.text:
                            try:
                                old_price = float(value_elem.text)
                                new_price = old_price + markup
                                value_elem.text = str(new_price)
                                updated_count += 1
                            except (ValueError, TypeError):
                                pass
            
            # Сохраняем изменения
            tree.write(sheet_path, encoding='utf-8', xml_declaration=True)
            return updated_count
            
        except Exception as e:
            logger.error(f"Ошибка при обработке листа {sheet_path}: {e}")
            return 0
    
    @staticmethod
    def _column_number_to_letter(column_number: int) -> str:
        """Конвертирует номер колонки в букву (1->A, 2->B, 27->AA, и т.д.)"""
        result = []
        while column_number > 0:
            column_number -= 1
            result.append(chr(column_number % 26 + ord('A')))
            column_number //= 26
        return ''.join(reversed(result))


# Тест функции
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    # Пример использования
    processor = XlsxImagePreservingProcessor()
    updated = processor.update_prices_in_xlsx(
        input_file="test_input.xlsx",
        output_file="test_output.xlsx",
        markup=200,
        price_column=4,
        header_row=5
    )
    print(f"Обновлено цен: {updated}")


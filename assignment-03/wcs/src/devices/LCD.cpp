#include "LCD.hpp"

#include "config.hpp"
#include "kernel/Logger.hpp"

#define MAX_WORDS 4
#define MAX_WORD_LEN 10

LCD::LCD(uint8_t addr, uint8_t cols, uint8_t rows)
{
    _lcd = new LiquidCrystal_I2C(addr, cols, rows);
    _lcd->init();
    _lcd->backlight();
    _cols = cols;
    _rows = rows;
}

void LCD::print(const char* message)
{
    this->clear();
    if (message == nullptr || message[0] == '\0')
        return;

    int maxChars = this->_cols * this->_rows;
    (void)maxChars;  // keep if you want to add truncation logic later

    _lcd->setCursor(0, 0);

    // Split into words safely (bounded buffers)
    char words[MAX_WORDS][MAX_WORD_LEN];
    int num_words = 0;
    int wpos = 0;

    for (int i = 0; message[i] != '\0' && num_words < MAX_WORDS; ++i)
    {
        char c = message[i];
        if (c == ' ')
        {
            if (wpos > 0)
            {
                words[num_words][wpos] = '\0';
                num_words++;
                wpos = 0;
            }
        }
        else
        {
            if (wpos < MAX_WORD_LEN - 1)
            {
                words[num_words][wpos++] = c;
            }
            else
            {
                // truncate the word if it's too long; skip remaining chars of this word
                while (message[i + 1] != '\0' && message[i + 1] != ' ') ++i;
                words[num_words][wpos] = '\0';
                num_words++;
                wpos = 0;
            }
        }
    }

    if (wpos > 0 && num_words < MAX_WORDS)
    {
        words[num_words][wpos] = '\0';
        num_words++;
    }

    int idx = 0;
    int current_line = 0;
    int current_line_chars = 0;

    while (idx < num_words && current_line < this->_rows)
    {
        size_t wlen = strlen(words[idx]);

        if (current_line_chars == 0)
        {
            if ((int)wlen <= this->_cols)
            {
                _lcd->print(words[idx]);
                current_line_chars = (int)wlen;
                idx++;
            }
            else
            {
                // Word longer than a line: print a truncated prefix
                char buf[33];
                int tocopy =
                    this->_cols < (int)sizeof(buf) - 1 ? this->_cols : (int)sizeof(buf) - 1;
                strncpy(buf, words[idx], tocopy);
                buf[tocopy] = '\0';
                _lcd->print(buf);
                idx++;  // drop the rest of the long word
                current_line++;
                if (current_line < this->_rows)
                    _lcd->setCursor(0, current_line);
                current_line_chars = 0;
            }
        }
        else
        {
            // Need a space before the next word
            if (current_line_chars + 1 + (int)wlen <= this->_cols)
            {
                _lcd->print(" ");
                _lcd->print(words[idx]);
                current_line_chars += 1 + (int)wlen;
                idx++;
            }
            else
            {
                // move to next line
                current_line++;
                if (current_line >= this->_rows)
                    break;
                _lcd->setCursor(0, current_line);
                current_line_chars = 0;
            }
        }
    }
}

void LCD::clear() { _lcd->clear(); }
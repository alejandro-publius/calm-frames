// Render the repository's SVG artwork with the installed Qt SVG engine.
// No browser, screen capture or network is involved.
// Build-only source stays outside app/assets, which the native package ships.
#include <QGuiApplication>
#include <QImage>
#include <QPainter>
#include <QSvgRenderer>
#include <QString>
#include <QFontDatabase>
#include <QDir>
#include <QFileInfo>

int main(int argc, char **argv) {
    QGuiApplication app(argc, argv);
    if (argc != 5) return 2;
    QDir fonts(QFileInfo(QString::fromLocal8Bit(argv[1])).absolutePath() + "/../fonts");
    for (const auto &file : fonts.entryList({"*.ttf"}, QDir::Files))
        QFontDatabase::addApplicationFont(fonts.filePath(file));
    QSvgRenderer svg(QString::fromLocal8Bit(argv[1]));
    const int width = QString::fromLocal8Bit(argv[2]).toInt();
    const int height = QString::fromLocal8Bit(argv[3]).toInt();
    if (!svg.isValid() || width <= 0 || height <= 0) return 2;
    QImage image(width, height, QImage::Format_ARGB32_Premultiplied);
    image.fill(Qt::transparent);
    QPainter painter(&image);
    painter.setRenderHint(QPainter::Antialiasing);
    svg.render(&painter);
    painter.end();
    // The listing tile has an opaque teal ground and ships without alpha.
    if (width == 1280 && height == 720) image = image.convertToFormat(QImage::Format_RGB888);
    return image.save(QString::fromLocal8Bit(argv[4]), "PNG") ? 0 : 1;
}

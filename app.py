import sys
import objc
from Cocoa import *
from Quartz import *
from PyObjCTools import AppHelper
from CoreServices import kUTTypePNG
from ai import AnalyzeImage
import os
import json
from loguru import logger
import sys
from Foundation import NSObject, NSThread
from AppKit import NSSound
import logging
import re

def set_global_logging_level(level=logging.ERROR, prefices=[""]):
    prefix_re = re.compile(fr'^(?:{ "|".join(prefices) })')
    for name in logging.root.manager.loggerDict:
        if re.match(prefix_re, name):
            logging.getLogger(name).setLevel(level)

set_global_logging_level(logging.ERROR)

current_row = 0

# When adding a new game make them parameters
platform = "snes"
game = "chrono_trigger"
game_dict = json.load(open(f'games/{platform}/{game}/dict.json'))


def keyboardCallback(proxy, type_, event, refcon):
    global current_row
    appDelegate = refcon
    keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
    
    if keycode == 17:  # T key to translate
        print("T key pressed")
        appDelegate.overlayView.startLoading()
        appDelegate.overlayWindow.display()
        
        # Start analysis in background thread
        NSThread.detachNewThreadSelector_toTarget_withObject_(
            'performAnalysis:', 
            appDelegate, 
            None
        )
    
    elif keycode == 35:  # P play audio
        print(f"Playing sound file for row {current_row}")
        sound_file = f"games/{platform}/{game}/sounds/{current_row}.wav"  # Adjust path as needed
        if os.path.exists(sound_file):
            sound = NSSound.alloc().initWithContentsOfFile_byReference_(sound_file, True)
            if sound:
                sound.play()
            else:
                print(f"Failed to load sound file: {sound_file}")
        else:
            print(f"Sound file not found: {sound_file}")

    return event

class AppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        self.createOverlayWindow()
        self.startEventTap()

    def createOverlayWindow(self):
        overlay_width = 1500
        overlay_height = 836
        overlay_x = 0
        overlay_y = 107

        frame = NSMakeRect(overlay_x, overlay_y, overlay_width, overlay_height)

        self.overlayWindow = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered,
            False
        )
        self.overlayWindow.setBackgroundColor_(NSColor.clearColor())
        self.overlayWindow.setLevel_(NSPopUpMenuWindowLevel)
        self.overlayWindow.setIgnoresMouseEvents_(True)
        self.overlayWindow.setOpaque_(False)

        self.overlayView = OverlayView.alloc().initWithFrame_(frame)
        self.overlayWindow.setContentView_(self.overlayView)
        
        self.overlayWindow.makeKeyAndOrderFront_(None)
    
    def updateText_(self, text_dict):
        self.overlayView.japanese_text = text_dict['japanese']
        self.overlayView.english_text = text_dict['english']
        if 'analysis' in text_dict and 'array' in text_dict['analysis']:
            self.overlayView.word_analysis = text_dict['analysis']['array']
        else:
            self.overlayView.word_analysis = []
        self.overlayView.setNeedsDisplay_(True)
        self.overlayWindow.display()  # Force window update
    
    def captureScreenshot(self):
        top_value = 350
        bottom_value = 80

        region_height = abs(top_value - bottom_value)
        min_value = min(top_value, bottom_value)
        screen_rect = CGRectMake(610, 400 + min_value, 870, region_height - 50)  # Adjust X and width as needed

        # Capture the screenshot of the defined area
        image_ref = CGWindowListCreateImage(
            screen_rect,
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID,
            kCGWindowImageDefault
        )
        if image_ref is None:
            print("Failed to capture screenshot.")
            return

        # Save the image to disk
        destination = "screenshot.png"  # Change to a path with known write permissions
        url = NSURL.fileURLWithPath_(destination)

        dest = CGImageDestinationCreateWithURL(url, kUTTypePNG, 1, None)
        if dest is None:
            print("Failed to create image destination.")
            return

        CGImageDestinationAddImage(dest, image_ref, None)
        if not CGImageDestinationFinalize(dest):
            print("Failed to finalize the image destination.")
            return
   
    def startEventTap(self):
        eventMask = CGEventMaskBit(kCGEventKeyDown)
        self.eventTap = CGEventTapCreate(
            kCGSessionEventTap,
            kCGHeadInsertEventTap,
            kCGEventTapOptionListenOnly,
            eventMask,
            keyboardCallback,
            self
        )
        if not self.eventTap:
            print("Failed to create event tap. Ensure the script has Accessibility permissions.")
            sys.exit(1)
        
        runLoopSource = CFMachPortCreateRunLoopSource(None, self.eventTap, 0)
        CFRunLoopAddSource(CFRunLoopGetCurrent(), runLoopSource, kCFRunLoopCommonModes)
        CGEventTapEnable(self.eventTap, True)

    def performAnalysis_(self, sender):
        global current_row
        try:
            self.captureScreenshot()
            analyze_image = AnalyzeImage(platform=platform, game=game)
            best_match, best_match_dict = analyze_image.analyze("screenshot.png")
            current_row = best_match['row']
            analysis = game_dict[str(current_row)]['analysis']
            
            # Update UI on main thread
            self.performSelectorOnMainThread_withObject_waitUntilDone_(
                'updateText:', 
                {'japanese': best_match['japanese'], 
                 'english': best_match['english'], 
                 "analysis": analysis},
                True
            )
        finally:
            self.performSelectorOnMainThread_withObject_waitUntilDone_(
                'hideLoading', 
                None,
                True
            )

    def hideLoading(self):
        self.overlayView.stopLoading()
        self.overlayWindow.display()

class OverlayView(NSView):
    def initWithFrame_(self, frame):
        try:
            self = objc.super(OverlayView, self).initWithFrame_(frame)
            if self:
                self.japanese_text = "日本語のテキスト"
                self.english_text = "English text"
                self.word_analysis = []
                self.is_loading = False  # Add loading state
            return self
        except Exception as e:
            print(f"Error in initWithFrame_: {e}")
            raise

    def startLoading(self):
        self.is_loading = True
        self.setNeedsDisplay_(True)

    def stopLoading(self):
        self.is_loading = False
        self.setNeedsDisplay_(True)

    def drawRect_(self, rect):
        try:
            # Calculate dimensions
            analysis_width = 600  # Width for the analysis section
            padding = 10
            corner_radius = 10
            
            # Header dimensions
            header_height = 40
            header_x = padding
            header_y = self.frame().size.height - header_height - padding
            header_width = analysis_width - (padding * 2)
            
            # Grid body dimensions
            grid_body_height = self.frame().size.height - header_height - (padding * 4)
            grid_x = padding
            grid_y = padding
            grid_width = analysis_width - (padding * 2)

            # Draw header rounded rectangle
            header_rect = NSMakeRect(header_x, header_y, header_width, header_height)
            header_path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                header_rect, corner_radius, corner_radius
            )
            
            # Draw with specific RGBA, create a color object
            header_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.105, 0.6, 0.66, 1.0)
            header_color.setFill()
            header_path.fill()
            
            # Draw gray border for header
            NSColor.colorWithCalibratedRed_green_blue_alpha_(0.105, 0.6, 0.66, 1.0).setStroke()
            header_path.setLineWidth_(2.0)
            header_path.stroke()

            # Draw grid body rounded rectangle
            grid_rect = NSMakeRect(grid_x, grid_y, grid_width, grid_body_height)
            grid_path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                grid_rect, corner_radius, corner_radius
            )
            
            # Draw white background for grid body
            NSColor.whiteColor().setFill()
            grid_path.fill()
            
            # Draw gray border for grid body
            NSColor.colorWithCalibratedRed_green_blue_alpha_(0.105, 0.6, 0.66, 1.0).setStroke()
            grid_path.setLineWidth_(5.0)
            grid_path.stroke()

            # Set up text attributes for headers
            header_attributes = {
                NSFontAttributeName: NSFont.boldSystemFontOfSize_(14),
                NSForegroundColorAttributeName: NSColor.blackColor()
            }
            
            # Calculate column widths
            col_width = (grid_width - (padding * 4)) / 3  # Divide into 3 columns

            # Draw headers
            headers = ["TEXT", "HIRAGANA", "ENGLISH"]
            for i, header in enumerate(headers):
                x_pos = header_x + padding + (i * (col_width + padding))
                y_pos = header_y + (header_height - 25)  # Centered in header rect
                NSString.stringWithString_(header).drawAtPoint_withAttributes_(
                    NSPoint(x_pos, y_pos),
                    header_attributes
                )

            # Draw grid content with different fonts for each column
            kanji_attributes = {
                NSFontAttributeName: NSFont.fontWithName_size_("Hiragino Kaku Gothic ProN", 20),
                NSForegroundColorAttributeName: NSColor.blackColor()
            }

            hiragana_attributes = {
                NSFontAttributeName: NSFont.fontWithName_size_("Hiragino Maru Gothic ProN", 20),
                NSForegroundColorAttributeName: NSColor.blackColor()
            }

            english_translation_attributes = {
                NSFontAttributeName: NSFont.fontWithName_size_("Avenir", 20),
                NSForegroundColorAttributeName: NSColor.blackColor()
            }

            # Draw the word grid
            row_height = 35
            start_y = grid_y + grid_body_height - row_height - padding
            
            # Set up line color and width
            NSColor.grayColor().setStroke()
            
            for i, word_info in enumerate(self.word_analysis):
                y_pos = start_y - (i * row_height)
                
                # Draw Japanese word
                NSString.stringWithString_(word_info.get('word', '')).drawAtPoint_withAttributes_(
                    NSPoint(grid_x + padding, y_pos),
                    kanji_attributes
                )
                
                # Draw Hiragana
                NSString.stringWithString_(word_info.get('hiragana', '')).drawAtPoint_withAttributes_(
                    NSPoint(grid_x + padding * 2 + col_width, y_pos),
                    hiragana_attributes
                )
                
                # Draw English meaning
                NSString.stringWithString_(word_info.get('meaning', '')).drawAtPoint_withAttributes_(
                    NSPoint(grid_x + padding * 3 + col_width * 2, y_pos),
                    english_translation_attributes
                )
                
                # Draw horizontal line below this row
                line_y = y_pos - (row_height / 4)  # Position line between rows
                line_path = NSBezierPath.bezierPath()
                line_path.setLineWidth_(1.0)  # Set line thickness
                line_path.moveToPoint_(NSPoint(grid_x + padding, line_y))
                line_path.lineToPoint_(NSPoint(grid_x + grid_width - padding, line_y))
                line_path.stroke()

            # Draw bottom text area with rounded rectangle
            bottom_height = 100
            bottom_width = self.frame().size.width - 20  # Padding on sides
            bottom_x = 10  # Padding from left
            bottom_y = 10  # Padding from bottom
            corner_radius = 10
            
            # Create the rounded rectangle path
            bottom_rect = NSMakeRect(bottom_x, bottom_y, bottom_width, bottom_height)
            bottom_path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                bottom_rect, corner_radius, corner_radius
            )
            
            # Draw white background
            NSColor.whiteColor().setFill()
            bottom_path.fill()
            
            # Draw gray border
            #NSColor.grayColor().setStroke()
            NSColor.colorWithCalibratedRed_green_blue_alpha_(0.105, 0.6, 0.66, 1.0).setStroke()
            bottom_path.setLineWidth_(5.0)
            bottom_path.stroke()

            # Create different text attributes for Japanese and English
            japanese_attributes = {
                NSFontAttributeName: NSFont.fontWithName_size_("Hiragino Kaku Gothic ProN", 20),  # Japanese font
                NSForegroundColorAttributeName: NSColor.blackColor()
            }
            
            english_attributes = {
                NSFontAttributeName: NSFont.fontWithName_size_("Avenir", 20),  # English font
                NSForegroundColorAttributeName: NSColor.blackColor()
            }

            # Draw "Working..." text if loading
            if self.is_loading:
                working_attributes = {
                    NSFontAttributeName: NSFont.fontWithName_size_("Helvetica Neue", 16),
                    NSForegroundColorAttributeName: NSColor.colorWithCalibratedRed_green_blue_alpha_(0.105, 0.6, 0.66, 1.0)
                }
                
                working_text = NSString.stringWithString_("Processing...")
                # Position in bottom-right corner of bottom rect
                text_x = bottom_x + bottom_width - 100  # Adjust based on text width
                text_y = bottom_y + (bottom_height - 20) / 2  # Centered vertically
                
                working_text.drawAtPoint_withAttributes_(
                    NSPoint(text_x, text_y),
                    working_attributes
                )
                
            # Draw the Japanese and English text with their specific fonts
            text_japanese = NSString.stringWithString_(self.japanese_text)
            text_english = NSString.stringWithString_(self.english_text)
            
            text_point_japanese = NSPoint(bottom_x + 20, bottom_y + 60)
            text_point_english = NSPoint(bottom_x + 20, bottom_y + 20)
            
            text_japanese.drawAtPoint_withAttributes_(text_point_japanese, japanese_attributes)
            text_english.drawAtPoint_withAttributes_(text_point_english, english_attributes)

        except Exception as e:
            print(f"Error in drawRect_: {e}")
            raise

if __name__ == "__main__":
    app = NSApplication.sharedApplication()
    try:
        app = NSApplication.sharedApplication()
        delegate = AppDelegate.alloc().init()
        app.setDelegate_(delegate)
        
        app.run()
        
    except Exception as e:
        print(f"Error in main: {e}")
        raise
    app.setDelegate_(delegate)
    AppHelper.runEventLoop()
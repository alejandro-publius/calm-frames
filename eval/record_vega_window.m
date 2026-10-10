// Actual simulator capture via macOS ScreenCaptureKit. Zero seconds saves PNG.
// Requires macOS 15 and Screen Recording permission. Does not alter the app.
#import <Foundation/Foundation.h>
#import <AppKit/AppKit.h>
#import <ScreenCaptureKit/ScreenCaptureKit.h>
#import <AVFoundation/AVFoundation.h>
@interface Recorder : NSObject <SCRecordingOutputDelegate, SCStreamDelegate>
@property SCStream *stream;
@property int seconds;
@end
@implementation Recorder
- (void)recordingOutputDidStartRecording:(SCRecordingOutput *)o { fprintf(stderr,"recording started\n"); dispatch_after(dispatch_time(DISPATCH_TIME_NOW,(int64_t)self.seconds*NSEC_PER_SEC),dispatch_get_main_queue(),^{ [self.stream stopCaptureWithCompletionHandler:^(NSError *e){if(e) {NSLog(@"stop %@",e);exit(3);}}]; }); }
- (void)recordingOutputDidFinishRecording:(SCRecordingOutput *)o {fprintf(stderr,"recording finished\n");exit(0);}
- (void)recordingOutput:(SCRecordingOutput *)o didFailWithError:(NSError *)e {NSLog(@"recording error %@",e);exit(4);}
- (void)stream:(SCStream *)s didStopWithError:(NSError *)e {NSLog(@"stream error %@",e);exit(5);}
@end
int main(int argc,const char **argv) { @autoreleasepool {
 [NSApplication sharedApplication];
 if(argc!=3){fprintf(stderr,"usage: calm-record-window OUTPUT.mp4 SECONDS\n");return 2;}
 NSString *path=[NSString stringWithUTF8String:argv[1]]; Recorder *r=[Recorder new]; r.seconds=atoi(argv[2]);
 if(r.seconds<0 || r.seconds>600){fprintf(stderr,"seconds must be 0..600\n");return 2;}
 [SCShareableContent getShareableContentExcludingDesktopWindows:YES onScreenWindowsOnly:NO completionHandler:^(SCShareableContent *c,NSError *e){
 if(e){NSLog(@"content error %@",e);exit(6);} SCWindow *target=nil;
 for(SCWindow *w in c.windows) if([w.title isEqualToString:@"Vega Virtual Device"]){target=w;break;}
 if(!target){fprintf(stderr,"no Vega window\n");exit(7);} NSLog(@"Vega window id=%u frame=%@",target.windowID,NSStringFromRect(target.frame));
 // Bring the target forward so Stage Manager does not return an old GPU frame.
 [[NSRunningApplication runningApplicationWithProcessIdentifier:target.owningApplication.processID] activateWithOptions:0];
 dispatch_after(dispatch_time(DISPATCH_TIME_NOW,NSEC_PER_SEC),dispatch_get_main_queue(),^{
 SCContentFilter *f=[[SCContentFilter alloc] initWithDesktopIndependentWindow:target];
 SCStreamConfiguration *cfg=[SCStreamConfiguration new];cfg.width=1920;cfg.height=1080;cfg.minimumFrameInterval=CMTimeMake(1,30);cfg.showsCursor=NO;cfg.capturesAudio=YES;cfg.excludesCurrentProcessAudio=YES;cfg.sampleRate=48000;cfg.channelCount=2;
 if(r.seconds==0) { [SCScreenshotManager captureImageWithFilter:f configuration:cfg completionHandler:^(CGImageRef im,NSError *err){if(err){NSLog(@"screenshot error %@",err);exit(11);} NSBitmapImageRep *rep=[[NSBitmapImageRep alloc]initWithCGImage:im]; [[rep representationUsingType:NSBitmapImageFileTypePNG properties:@{}] writeToFile:path atomically:YES];exit(0);}];return;}
 r.stream=[[SCStream alloc]initWithFilter:f configuration:cfg delegate:r];
 SCRecordingOutputConfiguration *out=[SCRecordingOutputConfiguration new];out.outputURL=[NSURL fileURLWithPath:path];out.videoCodecType=AVVideoCodecTypeH264;out.outputFileType=AVFileTypeMPEG4;
 SCRecordingOutput *rec=[[SCRecordingOutput alloc]initWithConfiguration:out delegate:r];NSError *err=nil;
 if(![r.stream addRecordingOutput:rec error:&err]){NSLog(@"add error %@",err);exit(8);}
 [r.stream startCaptureWithCompletionHandler:^(NSError *err){if(err){NSLog(@"start error %@",err);exit(9);}}];
 });
 }];
 dispatch_after(dispatch_time(DISPATCH_TIME_NOW,(r.seconds+30)*NSEC_PER_SEC),dispatch_get_main_queue(),^{fprintf(stderr,"recording timeout\n");exit(10);});
 [[NSRunLoop mainRunLoop]run];
 } return 0; }

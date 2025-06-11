package com.authzed;

import com.authzed.api.materialize.v0.Cursor;
import com.authzed.api.materialize.v0.LookupPermissionSetsRequest;
import com.authzed.api.materialize.v0.WatchPermissionSetsRequest;
import com.authzed.api.materialize.v0.WatchPermissionSetsServiceGrpc;
import com.authzed.api.v1.ZedToken;
import com.authzed.grpcutil.BearerToken;
import com.google.protobuf.TextFormat;
import io.grpc.ManagedChannel;
import io.grpc.netty.shaded.io.grpc.netty.GrpcSslContexts;
import io.grpc.netty.shaded.io.grpc.netty.NettyChannelBuilder;
import io.grpc.netty.shaded.io.netty.handler.ssl.util.InsecureTrustManagerFactory;

import javax.net.ssl.SSLException;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

public class MaterializeClient {

    private static final String BEARER_TOKEN = "sdbpk_62592e884be49ff6eeee54c4a65585169317d163827c35203948773f340fc3390e981b8df2c89033439be3b4d5dbb6d16b82baad81fbbdd301b4b1ea06b66f99e2c8d3d2ce686a84c9a80ce08bbbd746d1039823fb9de2be2bec7df87e69e7f8";
    private static final String SERVER_HOST = "localhost";
    private static final int SERVER_PORT = 50054;
    private static final String CURSOR_FILE = "cursor.txt";
    private static final String ZED_TOKEN_FILE = "zed_token.txt";
    private static final int PAGE_LIMIT = 10000;

    public static void main(String[] args) throws InterruptedException, SSLException {

        WatchPermissionSetsServiceGrpc.WatchPermissionSetsServiceStub stub = buildWatchPermissionSetsServiceStub();

        System.out.println("Starting LookupPermissionSets...");
        lookupPermissionSets(stub);

        System.out.println("Starting WatchPermissionSets...");
        watchPermissionSets(stub);
    }

    private static void lookupPermissionSets(WatchPermissionSetsServiceGrpc.WatchPermissionSetsServiceStub stub) throws InterruptedException {
        final CountDownLatch[] pageLatch = {new CountDownLatch(1)};
        AtomicBoolean lastPage = new AtomicBoolean(false);

        LookupPermissionSetsStreamObserver responseStreamObserver = new LookupPermissionSetsStreamObserver(
                pageLatch, lastPage, PAGE_LIMIT);

        LookupPermissionSetsRequest request = LookupPermissionSetsRequest.newBuilder().setLimit(PAGE_LIMIT)
                .build();

        // Initial call to LPS, without any cursor.
        stub.lookupPermissionSets(request, responseStreamObserver);
        pageLatch[0].await();

        // Page through results, using cursor to iterate through pages.
        while (!lastPage.get()) {
            pageLatch[0] = new CountDownLatch(1);
            request = LookupPermissionSetsRequest.newBuilder().setLimit(PAGE_LIMIT).setOptionalStartingAfterCursor(readCursorFromFile())
                    .build();
            stub.lookupPermissionSets(request, responseStreamObserver);
            pageLatch[0].await();
        }
    }

    private static void watchPermissionSets(WatchPermissionSetsServiceGrpc.WatchPermissionSetsServiceStub stub) {

        WatchPermissionSetsStreamObserver responseStreamObserver = new WatchPermissionSetsStreamObserver();

        Cursor cursor = readCursorFromFile();

        WatchPermissionSetsRequest.Builder requestBuilder = WatchPermissionSetsRequest.newBuilder();
        if (cursor != null) {
            requestBuilder.setOptionalStartingAfter(cursor.getToken());
        }
        WatchPermissionSetsRequest request = requestBuilder.build();

        stub.watchPermissionSets(request, responseStreamObserver);

        // Keep the main thread alive to maintain the stream
        try {
            Thread.sleep(Long.MAX_VALUE);
        } catch (InterruptedException e) {
            System.out.println("Stream interrupted");
        }

    }

    private static WatchPermissionSetsServiceGrpc.WatchPermissionSetsServiceStub buildWatchPermissionSetsServiceStub() throws SSLException {
        BearerToken bearerToken = new BearerToken(BEARER_TOKEN);
        ManagedChannel channel = NettyChannelBuilder.forAddress(SERVER_HOST, SERVER_PORT)
                .sslContext(GrpcSslContexts.forClient()
                        .trustManager(InsecureTrustManagerFactory.INSTANCE)
                        .build())
                .build();

        return WatchPermissionSetsServiceGrpc.newStub(channel)
                .withCallCredentials(bearerToken);
    }

    private static Cursor readCursorFromFile() {
        try {
            String content = Files.readString(Paths.get(CURSOR_FILE));
            Cursor.Builder cursorBuilder = Cursor.newBuilder();
            TextFormat.merge(content, cursorBuilder);
            return cursorBuilder.build();
        } catch (Exception e) {
            System.out.println("Could not read or parse cursor.txt file: " + e.getMessage());
            return null;
        }
    }

    static void writeCursorToFile(Cursor cursor) {
        try (FileWriter writer = new FileWriter(CURSOR_FILE, false)) {
            writer.write(cursor.toString());
        } catch (IOException e) {
            System.err.println("Error writing cursor to file: " + e.getMessage());
        }
    }

    static void writeZedTokenToFile(ZedToken zedToken) {
        try (FileWriter writer = new FileWriter(ZED_TOKEN_FILE, false)) {
            writer.write(zedToken.toString());
        } catch (IOException e) {
            System.err.println("Error writing zed token to file: " + e.getMessage());
        }
    }

    private static ZedToken readZedTokenFromFile() {
        try {
            String content = Files.readString(Paths.get(CURSOR_FILE));
            ZedToken.Builder zedTokenBuilder = ZedToken.newBuilder();
            TextFormat.merge(content, zedTokenBuilder);
            return zedTokenBuilder.build();
        } catch (Exception e) {
            System.out.println("Could not read or parse zed_token.txt file: " + e.getMessage());
            return null;
        }
    }

    static void printCounts(AtomicInteger memberToSetRecordCount, AtomicInteger overallRecordCount, AtomicInteger recordCount, AtomicInteger setToSetRecordCount) {
        System.out.printf("RecordCount: %d.  OverallRecordCount: %d. MemberToSetCount: %d.  SetToSetCount: %d.\n",
                recordCount.get(),
                overallRecordCount.get(),
                memberToSetRecordCount.get(),
                setToSetRecordCount.get()
        );
    }
}

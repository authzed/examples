package com.authzed;

import com.authzed.api.materialize.v0.WatchPermissionSetsResponse;
import com.authzed.api.materialize.v0.PermissionSetChange;
import com.authzed.api.v1.ZedToken;
import io.grpc.StatusRuntimeException;
import io.grpc.stub.StreamObserver;

import java.util.concurrent.atomic.AtomicInteger;

import static com.authzed.MaterializeClient.printCounts;
import static com.authzed.MaterializeClient.writeZedTokenToFile;


public class WatchPermissionSetsStreamObserver implements StreamObserver<WatchPermissionSetsResponse> {
    private final AtomicInteger recordCount = new AtomicInteger(0);
    private final AtomicInteger memberToSetRecordCount = new AtomicInteger(0);
    private final AtomicInteger setToSetRecordCount = new AtomicInteger(0);

    @Override
    public void onNext(WatchPermissionSetsResponse response) {
        ZedToken zedToken = response.getCompletedRevision();
        writeZedTokenToFile(zedToken);

        recordCount.incrementAndGet();

        PermissionSetChange permissionSetChange = response.getChange();
        if (permissionSetChange.getOperation() == PermissionSetChange.SetOperation.SET_OPERATION_ADDED ||
                permissionSetChange.getOperation() == PermissionSetChange.SetOperation.SET_OPERATION_REMOVED) {
            if (permissionSetChange.hasChildMember()) {
                memberToSetRecordCount.incrementAndGet();
                printCounts(memberToSetRecordCount, recordCount, recordCount, setToSetRecordCount);
            } else {
                setToSetRecordCount.incrementAndGet();
                printCounts(memberToSetRecordCount, recordCount, recordCount, setToSetRecordCount);
            }
        }
    }

    @Override
    public void onError(Throwable throwable) {
        System.out.printf("Watch permission sets api error %s%n",
            throwable instanceof StatusRuntimeException ?
            ((StatusRuntimeException) throwable).getStatus() : throwable.getMessage());
    }

    @Override
    public void onCompleted() {
        System.out.println("Stream completed");
        printCounts(memberToSetRecordCount, recordCount, recordCount, setToSetRecordCount);
    }
}
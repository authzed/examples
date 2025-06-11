package com.authzed;

import com.authzed.api.materialize.v0.Cursor;
import com.authzed.api.materialize.v0.LookupPermissionSetsResponse;
import com.authzed.api.materialize.v0.PermissionSetChange;
import io.grpc.StatusRuntimeException;
import io.grpc.stub.StreamObserver;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

import static com.authzed.MaterializeClient.printCounts;
import static com.authzed.MaterializeClient.writeCursorToFile;


public class LookupPermissionSetsStreamObserver implements StreamObserver<LookupPermissionSetsResponse> {
        private final Cursor[] cursor = {null};
        private final CountDownLatch[] pageLatch;
        private final int pageLimit;
        private final AtomicBoolean lastPage;
        private final AtomicInteger recordCount = new AtomicInteger(0);
        private final AtomicInteger overallRecordCount = new AtomicInteger(0);
        private final AtomicInteger memberToSetRecordCount = new AtomicInteger(0);
        private final AtomicInteger setToSetRecordCount = new AtomicInteger(0);

        public LookupPermissionSetsStreamObserver(CountDownLatch[] pageLatch, AtomicBoolean lastPage, int pageLimit) {
            this.pageLatch = pageLatch;
            this.lastPage = lastPage;
            this.pageLimit = pageLimit;
        }

        @Override
        public void onNext(LookupPermissionSetsResponse response) {
            cursor[0] = response.getCursor();
            writeCursorToFile(cursor[0]);

            overallRecordCount.incrementAndGet();
            recordCount.incrementAndGet();

            PermissionSetChange permissionSetChange = response.getChange();
            if (permissionSetChange.getOperation() == PermissionSetChange.SetOperation.SET_OPERATION_ADDED) {
                if (permissionSetChange.hasChildMember()) {
                    memberToSetRecordCount.incrementAndGet();
                } else {
                    setToSetRecordCount.incrementAndGet();
                }
            }
        }

        @Override
        public void onError(Throwable throwable) {
            System.out.printf("Lookup permission sets api error %s%n",
                    throwable instanceof StatusRuntimeException ?
                            ((StatusRuntimeException) throwable).getStatus() : throwable.getMessage());
            if (cursor[0] != null) {
                System.out.println("Current cursor: " + cursor[0]);
            }
        }

        @Override
        public void onCompleted() {
            if (recordCount.get() == this.pageLimit) {
                printCounts(memberToSetRecordCount, overallRecordCount, recordCount, setToSetRecordCount);
                recordCount.set(0);
            } else {
                System.out.printf("Less than full page received, all pages complete. Record count: %s\n", recordCount.get());
                printCounts(memberToSetRecordCount, overallRecordCount, recordCount, setToSetRecordCount);
                lastPage.set(true);
            }
            pageLatch[0].countDown();
        }


    }